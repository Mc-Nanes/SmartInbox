from fastapi import UploadFile

from app.core.exceptions import InvalidInputError
from app.schemas.analysis import AnalysisResponse
from app.services.file_parser import FileParserService
from app.services.openai_email_analyzer import OpenAIEmailAnalyzerService
from app.services.text_preprocessor import TextPreprocessorService


class AnalysisOrchestratorService:
    def __init__(
        self,
        file_parser: FileParserService | None = None,
        text_preprocessor: TextPreprocessorService | None = None,
        openai_analyzer: OpenAIEmailAnalyzerService | None = None,
    ) -> None:
        self.file_parser = file_parser or FileParserService()
        self.text_preprocessor = text_preprocessor or TextPreprocessorService()
        self.openai_analyzer = openai_analyzer or OpenAIEmailAnalyzerService()

    def _merge_email_contents(self, email_body: str, attachment_content: str) -> str:
        sections: list[str] = []

        if email_body.strip():
            sections.append(f"[Corpo do email]\n{email_body.strip()}")

        if attachment_content.strip():
            sections.append(f"[Conteúdo do anexo]\n{attachment_content.strip()}")

        return "\n\n".join(sections)

    async def analyze(self, text: str | None = None, upload_file: UploadFile | None = None) -> AnalysisResponse:
        normalized_text = (text or "").strip()
        has_uploaded_file = upload_file is not None and bool(upload_file.filename)

        if not has_uploaded_file and not normalized_text:
            raise InvalidInputError("Informe o texto do email ou envie um arquivo válido.")

        source_text = normalized_text

        if has_uploaded_file and normalized_text:
            extracted_text = await self.file_parser.extract_text(upload_file)
            source_text = self._merge_email_contents(normalized_text, extracted_text)
        elif has_uploaded_file:
            source_text = await self.file_parser.extract_text(upload_file)

        preprocessed = self.text_preprocessor.preprocess(source_text)
        return self.openai_analyzer.analyze_email(
            original_text=preprocessed.original_text,
            normalized_text=preprocessed.normalized_text,
            processed_text=preprocessed.processed_text,
        )
