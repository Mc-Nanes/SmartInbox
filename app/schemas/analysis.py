from enum import Enum

from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    PRODUCTIVE = "Produtivo"
    UNPRODUCTIVE = "Improdutivo"


class AnalysisInput(BaseModel):
    text: str | None = None
    filename: str | None = None


class ClassificationResult(BaseModel):
    category: EmailCategory
    reason: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class AnalysisResponse(BaseModel):
    category: EmailCategory
    reason: str = Field(min_length=1)
    suggested_reply: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
