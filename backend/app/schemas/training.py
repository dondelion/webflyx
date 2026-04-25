import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.training_job import JobStatus, TrainingMode


class TrainingJobCreate(BaseModel):
    mode: TrainingMode = TrainingMode.zero_shot
    chunk_ids: list[uuid.UUID] | None = None


class TrainingJobOut(BaseModel):
    id: uuid.UUID
    voice_id: uuid.UUID
    mode: TrainingMode
    status: JobStatus
    progress: int
    celery_task_id: str | None
    model_path: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
