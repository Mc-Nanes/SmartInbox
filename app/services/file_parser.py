from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.exceptions import FileProcessingError, InvalidInputError


class FileParserService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def extract_text(self, upload_file: UploadFile) -> str:
        if upload_file is None or not upload_file.filename:
            raise InvalidInputError("Envie um arquivo .txt ou .pdf.")

        extension = Path(upload_file.filename).suffix.lower()
        if extension not in self.settings.allowed_extensions:
            raise InvalidInputError("Tipo de arquivo invalido. Use apenas .txt ou .pdf.")

        file_bytes = await upload_file.read()
        if not file_bytes:
            raise InvalidInputError("O arquivo enviado esta vazio.")

        if len(file_bytes) > self.settings.max_upload_size_bytes:
            raise InvalidInputError("O arquivo excede o limite permitido.")

        if extension == ".txt":
            return self._extract_text_from_txt(file_bytes)

        if extension == ".pdf":
            return self._extract_text_from_pdf(file_bytes)

        raise InvalidInputError("Tipo de arquivo nao suportado.")

    def _extract_text_from_txt(self, file_bytes: bytes) -> str:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FileProcessingError("Nao foi possivel ler o arquivo TXT enviado.") from exc

        if not text.strip():
            raise InvalidInputError("O arquivo TXT nao contem texto util.")

        return text

    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        try:
            from io import BytesIO

            reader = PdfReader(BytesIO(file_bytes))
            extracted_pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(extracted_pages).strip()
        except Exception as exc:
            raise FileProcessingError("PDF invalido ou corrompido.") from exc

        if not text:
            raise InvalidInputError("O PDF nao contem texto util.")

        return text
