import uuid
from datetime import datetime
from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    voice_id: uuid.UUID | None = None


class APIKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    voice_id: uuid.UUID | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyOut):
    raw_key: str
