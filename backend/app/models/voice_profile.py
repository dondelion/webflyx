import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Enum as SAEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class VoiceStatus(str, enum.Enum):
    created = "created"
    training = "training"
    ready = "ready"
    failed = "failed"


class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VoiceStatus] = mapped_column(
        SAEnum(VoiceStatus), default=VoiceStatus.created, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    samples: Mapped[list["AudioSample"]] = relationship(  # noqa: F821
        back_populates="voice", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[list["TrainingJob"]] = relationship(  # noqa: F821
        back_populates="voice", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(  # noqa: F821
        back_populates="voice", cascade="all, delete-orphan"
    )
    embedding: Mapped["VoiceEmbedding | None"] = relationship(  # noqa: F821
        back_populates="voice", cascade="all, delete-orphan", uselist=False
    )
