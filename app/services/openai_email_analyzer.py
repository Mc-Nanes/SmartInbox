import json
import re

from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import OpenAIIntegrationError, ServiceConfigurationError
from app.core.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    REPLY_SYSTEM_PROMPT,
    build_classification_prompt,
    build_reply_prompt,
)
from app.schemas.analysis import AnalysisResponse, ClassificationResult, EmailCategory


class OpenAIEmailAnalyzerService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def analyze_email(self, original_text: str, normalized_text: str, processed_text: str) -> AnalysisResponse:
        classification = self.classify_email(
            original_text=original_text,
            normalized_text=normalized_text,
            processed_text=processed_text,
        )
        suggested_reply = self.generate_suggested_reply(
            original_text=original_text,
            category=classification.category,
            reason=classification.reason,
        )

        return AnalysisResponse(
            category=classification.category,
            reason=classification.reason,
            suggested_reply=suggested_reply,
            confidence=classification.confidence,
        )

    def classify_email(
        self,
        original_text: str,
        normalized_text: str,
        processed_text: str,
    ) -> ClassificationResult:
        if not self.settings.openai_api_key:
            if self.settings.enable_local_ai_fallback:
                return self._classify_with_fallback(normalized_text=normalized_text, processed_text=processed_text)
            self._raise_missing_api_key()

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
            payload = self._parse_json_payload(response.output_text)
            return ClassificationResult.model_validate(payload)
        except OpenAIIntegrationError as exc:
            if self.settings.enable_local_ai_fallback:
                return self._classify_with_fallback(normalized_text=normalized_text, processed_text=processed_text)
            raise exc
        except Exception as exc:
            if self.settings.enable_local_ai_fallback:
                return self._classify_with_fallback(normalized_text=normalized_text, processed_text=processed_text)
            raise OpenAIIntegrationError("Falha ao classificar o email com a OpenAI.", status_code=502) from exc

    def generate_suggested_reply(self, original_text: str, category: EmailCategory, reason: str) -> str:
        if not self.settings.openai_api_key:
            if self.settings.enable_local_ai_fallback:
                return self._generate_reply_with_fallback(category=category, original_text=original_text)
            self._raise_missing_api_key()

        client = self._build_client()
        prompt = build_reply_prompt(email_text=original_text, category=category.value, reason=reason)

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
            if self.settings.enable_local_ai_fallback:
                return self._generate_reply_with_fallback(category=category, original_text=original_text)
            raise OpenAIIntegrationError("Falha ao gerar a resposta sugerida com a OpenAI.", status_code=502) from exc

        if not reply:
            if self.settings.enable_local_ai_fallback:
                return self._generate_reply_with_fallback(category=category, original_text=original_text)
            raise OpenAIIntegrationError("A OpenAI não retornou uma resposta sugerida válida.", status_code=502)

        return reply

    def _build_client(self) -> OpenAI:
        if not self.settings.openai_api_key:
            self._raise_missing_api_key()

        return OpenAI(api_key=self.settings.openai_api_key)

    def _parse_json_payload(self, response_text: str) -> dict:
        cleaned_text = response_text.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned_text, flags=re.DOTALL)
        if fenced_match:
            cleaned_text = fenced_match.group(1)
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            raise OpenAIIntegrationError(
                "A OpenAI retornou um JSON inválido para a classificação.",
                status_code=502,
            ) from exc

    def _classify_with_fallback(self, normalized_text: str, processed_text: str) -> ClassificationResult:
        productive_terms = {
            "status",
            "andamento",
            "prazo",
            "suporte",
            "erro",
            "falha",
            "problema",
            "duvida",
            "solicitacao",
            "documentacao",
            "documento",
            "aprovacao",
            "pagamento",
            "pendencia",
            "retorno",
            "analise",
            "processo",
            "demanda",
            "chamado",
            "urgente",
            "confirmacao",
            "ajuste",
            "revisao",
        }
        unproductive_terms = {
            "parabens",
            "obrigado",
            "obrigada",
            "agradeco",
            "felicitacoes",
            "cumprimentos",
            "saudacoes",
        }

        normalized_tokens = set(normalized_text.split())
        processed_tokens = set(processed_text.split())
        productive_score = len(productive_terms & normalized_tokens) + len(productive_terms & processed_tokens)
        unproductive_score = len(unproductive_terms & normalized_tokens)
        has_question = "?" in normalized_text

        if productive_score > 0 or has_question:
            confidence = min(0.95, 0.58 + productive_score * 0.08 + (0.08 if has_question else 0))
            return ClassificationResult(
                category=EmailCategory.PRODUCTIVE,
                reason="O email apresenta indícios de demanda operacional, necessidade de resposta ou acompanhamento.",
                confidence=round(confidence, 2),
            )

        if unproductive_score > 0:
            confidence = min(0.9, 0.62 + unproductive_score * 0.06)
            return ClassificationResult(
                category=EmailCategory.UNPRODUCTIVE,
                reason="O conteúdo indica uma mensagem cordial ou informativa, sem demanda prática imediata.",
                confidence=round(confidence, 2),
            )

        return ClassificationResult(
            category=EmailCategory.PRODUCTIVE,
            reason="Na ausência de sinais claros de informalidade, a classificação conservadora indica possível necessidade de tratamento.",
            confidence=0.55,
        )

    def _generate_reply_with_fallback(self, category: EmailCategory, original_text: str) -> str:
        preview = self._extract_preview(original_text)
        if category == EmailCategory.PRODUCTIVE:
            return (
                "Olá,\n\n"
                f"Obrigado pela mensagem sobre {preview}. O conteúdo foi recebido e pode ser tratado a partir "
                "das informações enviadas. Caso exista algum detalhe complementar relevante, ele pode ser "
                "encaminhado por este mesmo canal.\n\n"
                "Atenciosamente,"
            )

        return (
            "Olá,\n\n"
            "Obrigado pela mensagem. Agradecemos o contato e permanecemos à disposição caso surja "
            "alguma demanda adicional.\n\n"
            "Atenciosamente,"
        )

    def _extract_preview(self, original_text: str) -> str:
        cleaned_text = " ".join(original_text.strip().split())
        preview = cleaned_text[:70].strip(" ,.;:")
        if not preview:
            return "o tema informado"
        if len(cleaned_text) > 70:
            return f"{preview}..."
        return preview

    def _raise_missing_api_key(self) -> None:
        raise ServiceConfigurationError(
            "A variável de ambiente OPENAI_API_KEY não foi configurada e o fallback local está desabilitado.",
            status_code=500,
        )
