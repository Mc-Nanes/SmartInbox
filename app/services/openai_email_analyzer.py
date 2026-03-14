import json

from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import OpenAIIntegrationError, ServiceConfigurationError
from app.core.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    REPLY_SYSTEM_PROMPT,
    build_classification_prompt,
    build_reply_prompt,
)
from app.schemas.analysis import AnalysisResponse, ClassificationResult


class OpenAIEmailAnalyzerService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def analyze_email(self, original_text: str, processed_text: str) -> AnalysisResponse:
        classification = self.classify_email(original_text=original_text, processed_text=processed_text)
        suggested_reply = self.generate_suggested_reply(
            original_text=original_text,
            category=classification.category.value,
            reason=classification.reason,
        )

        return AnalysisResponse(
            category=classification.category,
            reason=classification.reason,
            suggested_reply=suggested_reply,
            confidence=classification.confidence,
        )

    def classify_email(self, original_text: str, processed_text: str) -> ClassificationResult:
        client = self._build_client()
        prompt = build_classification_prompt(email_text=original_text, processed_text=processed_text)

        try:
            response = client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            payload = json.loads(response.output_text)
            return ClassificationResult.model_validate(payload)
        except Exception as exc:
            raise OpenAIIntegrationError("Falha ao classificar o email com a OpenAI.", status_code=502) from exc

    def generate_suggested_reply(self, original_text: str, category: str, reason: str) -> str:
        client = self._build_client()
        prompt = build_reply_prompt(email_text=original_text, category=category, reason=reason)

        try:
            response = client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            reply = response.output_text.strip()
        except Exception as exc:
            raise OpenAIIntegrationError("Falha ao gerar a resposta sugerida com a OpenAI.", status_code=502) from exc

        if not reply:
            raise OpenAIIntegrationError("A OpenAI nao retornou uma resposta sugerida valida.", status_code=502)

        return reply

    def _build_client(self) -> OpenAI:
        if not self.settings.openai_api_key:
            raise ServiceConfigurationError(
                "A variavel de ambiente OPENAI_API_KEY nao foi configurada.",
                status_code=500,
            )

        return OpenAI(api_key=self.settings.openai_api_key)
