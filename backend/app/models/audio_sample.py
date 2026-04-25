import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AudioSample(Base):
    __tablename__ = "audio_samples"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    voice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("voice_profiles.id", ondelete="CASCADE"))
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    voice: Mapped["VoiceProfile"] = relationship(back_populates="samples")  # noqa: F821
    chunks: Mapped[list["AudioChunk"]] = relationship(  # noqa: F821
        back_populates="sample", cascade="all, delete-orphan"
    )
