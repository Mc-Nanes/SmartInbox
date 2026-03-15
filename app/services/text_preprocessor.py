import html
import re
import string
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlparse

from nltk.stem.snowball import SnowballStemmer

from app.core.exceptions import InvalidInputError

STOP_WORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "este",
    "esta",
    "isso",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "por",
    "que",
    "se",
    "sem",
    "ser",
    "sua",
    "suas",
    "seu",
    "seus",
    "uma",
    "umas",
    "um",
    "uns",
}

MAX_ANALYSIS_TEXT_CHARS = 5000
TRUNCATION_MARKER = "\n\n[trecho intermediário omitido para manter a análise objetiva]\n\n"


@dataclass(slots=True)
class PreprocessedText:
    original_text: str
    normalized_text: str
    tokens: list[str]
    processed_tokens: list[str]
    processed_text: str


class TextPreprocessorService:
    def __init__(self) -> None:
        self.stemmer = SnowballStemmer("portuguese")

    def preprocess(self, text: str) -> PreprocessedText:
        if not text or not text.strip():
            raise InvalidInputError("Informe um texto ou envie um arquivo válido.")

        sanitized_text = self._sanitize_text(text)
        normalized_text = self._normalize_text(sanitized_text)
        text_without_punctuation = self._remove_punctuation(normalized_text)
        tokens = self._tokenize(text_without_punctuation)
        filtered_tokens = self._remove_stop_words(tokens)
        processed_tokens = self._apply_stemming(filtered_tokens)

        if not processed_tokens:
            raise InvalidInputError("Não foi encontrado conteúdo útil após o pré-processamento.")

        return PreprocessedText(
            original_text=sanitized_text,
            normalized_text=normalized_text,
            tokens=tokens,
            processed_tokens=processed_tokens,
            processed_text=" ".join(processed_tokens),
        )

    def _sanitize_text(self, text: str) -> str:
        cleaned_text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n").strip()
        cleaned_text = self._strip_html(cleaned_text)
        cleaned_text = self._shorten_urls(cleaned_text)
        cleaned_text = self._normalize_noisy_blocks(cleaned_text)
        cleaned_text = self._normalize_spacing(cleaned_text)
        cleaned_text = self._safe_truncate(cleaned_text)

        if not cleaned_text.strip():
            raise InvalidInputError("Não foi encontrado conteúdo útil para análise.")

        return cleaned_text

    def _strip_html(self, text: str) -> str:
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</p\s*>", "\n\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        return html.unescape(text)

    def _shorten_urls(self, text: str) -> str:
        def replace_url(match: re.Match[str]) -> str:
            raw_url = match.group(0).rstrip(").,;")
            parsed = urlparse(raw_url)
            domain = parsed.netloc or parsed.path.split("/")[0]
            domain = domain.lower().replace("www.", "")
            if not domain:
                return "[link]"
            return f"[link:{domain}]"

        return re.sub(r"https?://\S+", replace_url, text, flags=re.IGNORECASE)

    def _normalize_noisy_blocks(self, text: str) -> str:
        normalized_lines: list[str] = []

        for raw_line in text.split("\n"):
            line = re.sub(r"[ \t]+", " ", raw_line).strip()
            if not line:
                normalized_lines.append("")
                continue

            if self._is_noisy_separator(line):
                continue

            line = re.sub(r"([!?._\-=*#])\1{3,}", r"\1\1\1", line)
            normalized_lines.append(line)

        return "\n".join(normalized_lines)

    def _is_noisy_separator(self, line: str) -> bool:
        if len(line) < 6:
            return False

        alnum_count = sum(character.isalnum() for character in line)
        return alnum_count == 0 or (alnum_count / len(line)) < 0.2

    def _normalize_spacing(self, text: str) -> str:
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _safe_truncate(self, text: str) -> str:
        if len(text) <= MAX_ANALYSIS_TEXT_CHARS:
            return text

        available_chars = MAX_ANALYSIS_TEXT_CHARS - len(TRUNCATION_MARKER)
        head_chars = int(available_chars * 0.6)
        tail_chars = available_chars - head_chars

        return f"{text[:head_chars].rstrip()}{TRUNCATION_MARKER}{text[-tail_chars:].lstrip()}"

    def _normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(character for character in text if not unicodedata.combining(character))
        return re.sub(r"\s+", " ", text)

    def _remove_punctuation(self, text: str) -> str:
        translator = str.maketrans("", "", string.punctuation)
        return text.translate(translator)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text)

    def _remove_stop_words(self, tokens: list[str]) -> list[str]:
        return [
            token
            for token in tokens
            if token not in STOP_WORDS and len(token) > 1 and not token.isdigit()
        ]

    def _apply_stemming(self, tokens: list[str]) -> list[str]:
        return [self.stemmer.stem(token) for token in tokens]
