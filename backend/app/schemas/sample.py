import uuid
from datetime import datetime
from pydantic import BaseModel


class SampleOut(BaseModel):
    id: uuid.UUID
    voice_id: uuid.UUID
    original_filename: str
    duration_sec: float | None
    sample_rate: int | None
    channels: int | None
    format: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
