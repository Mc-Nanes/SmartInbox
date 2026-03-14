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

    async def analyze(self, text: str | None = None, upload_file: UploadFile | None = None) -> AnalysisResponse:
        if upload_file is None and (text is None or not text.strip()):
            raise InvalidInputError("Informe o texto do email ou envie um arquivo valido.")

        source_text = text or ""
        if upload_file is not None:
            source_text = await self.file_parser.extract_text(upload_file)

        preprocessed = self.text_preprocessor.preprocess(source_text)
        return self.openai_analyzer.analyze_email(
            original_text=preprocessed.original_text,
            processed_text=preprocessed.processed_text,
        )
