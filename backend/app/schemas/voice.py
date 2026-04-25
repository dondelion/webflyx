import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.voice_profile import VoiceStatus


class VoiceCreate(BaseModel):
    name: str
    description: str | None = None


class VoiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class VoiceOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: VoiceStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
