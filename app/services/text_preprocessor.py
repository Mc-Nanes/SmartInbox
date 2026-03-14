import re
import string
import unicodedata
from dataclasses import dataclass

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

        normalized_text = self._normalize_text(text)
        text_without_punctuation = self._remove_punctuation(normalized_text)
        tokens = self._tokenize(text_without_punctuation)
        filtered_tokens = self._remove_stop_words(tokens)
        processed_tokens = self._apply_stemming(filtered_tokens)

        if not processed_tokens:
            raise InvalidInputError("Não foi encontrado conteúdo útil após o pré-processamento.")

        return PreprocessedText(
            original_text=text.strip(),
            normalized_text=normalized_text,
            tokens=tokens,
            processed_tokens=processed_tokens,
            processed_text=" ".join(processed_tokens),
        )

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
