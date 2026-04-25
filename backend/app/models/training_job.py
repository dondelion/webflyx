import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TrainingMode(str, enum.Enum):
    zero_shot = "zero_shot"
    finetune = "finetune"


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    voice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("voice_profiles.id", ondelete="CASCADE"))
    mode: Mapped[TrainingMode] = mapped_column(SAEnum(TrainingMode), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.queued, nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    voice: Mapped["VoiceProfile"] = relationship(back_populates="training_jobs")  # noqa: F821
