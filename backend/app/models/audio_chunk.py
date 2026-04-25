import uuid
from datetime import datetime
from sqlalchemy import Text, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AudioChunk(Base):
    __tablename__ = "audio_chunks"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    sample_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audio_samples.id", ondelete="CASCADE"))
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    phonemes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transcription_pending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sample: Mapped["AudioSample"] = relationship(back_populates="chunks")  # noqa: F821
