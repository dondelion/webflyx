import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class VoiceEmbedding(Base):
    __tablename__ = "voice_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    voice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("voice_profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    gpt_cond_latent_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    speaker_embedding_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    reference_audio_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    voice: Mapped["VoiceProfile"] = relationship(back_populates="embedding")  # noqa: F821
