import uuid
from pydantic import BaseModel


class PhonemeGap(BaseModel):
    phoneme: str
    example_word: str
    category: str


class CategoryCoverage(BaseModel):
    covered: list[str]
    missing: list[str]
    score: float


class ChunkSuggestion(BaseModel):
    chunk_id: uuid.UUID
    sample_id: uuid.UUID
    start_sec: float
    end_sec: float
    transcript: str | None
    fills_phonemes: list[str]
    gain: int


class CoverageReport(BaseModel):
    voice_id: uuid.UUID
    score: float
    covered_count: int
    total_count: int
    covered: list[str]
    missing: list[PhonemeGap]
    by_category: dict[str, CategoryCoverage]
    suggestions: list[ChunkSuggestion]
    suggested_sentences: list[str]
