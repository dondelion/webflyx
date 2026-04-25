import uuid
from datetime import datetime
from pydantic import BaseModel


class ChunkCreate(BaseModel):
    start_sec: float
    end_sec: float
    transcript: str | None = None
    selected: bool = False


class ChunkUpdate(BaseModel):
    transcript: str | None = None
    selected: bool | None = None


class ChunkOut(BaseModel):
    id: uuid.UUID
    sample_id: uuid.UUID
    start_sec: float
    end_sec: float
    transcript: str | None
    phonemes: list[str] | None
    selected: bool
    transcription_pending: bool
    created_at: datetime

    model_config = {"from_attributes": True}
