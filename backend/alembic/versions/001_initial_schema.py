"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-25
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voice_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("created", "training", "ready", "failed", name="voicestatus"),
            nullable=False,
            server_default="created",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voice_profiles.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audio_samples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voice_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("stored_filename", sa.String(512), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("duration_sec", sa.Float, nullable=True),
        sa.Column("sample_rate", sa.Integer, nullable=True),
        sa.Column("channels", sa.Integer, nullable=True),
        sa.Column("format", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audio_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "sample_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audio_samples.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_sec", sa.Float, nullable=False),
        sa.Column("end_sec", sa.Float, nullable=False),
        sa.Column("transcript", sa.Text, nullable=True),
        sa.Column("phonemes", postgresql.JSONB, nullable=True),
        sa.Column("selected", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("transcription_pending", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "training_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voice_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mode",
            sa.Enum("zero_shot", "finetune", name="trainingmode"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "completed", "failed", "cancelled", name="jobstatus"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("model_path", sa.String(1024), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "voice_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "voice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voice_profiles.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("gpt_cond_latent_path", sa.String(1024), nullable=False),
        sa.Column("speaker_embedding_path", sa.String(1024), nullable=False),
        sa.Column("reference_audio_path", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("voice_embeddings")
    op.drop_table("training_jobs")
    op.drop_table("audio_chunks")
    op.drop_table("audio_samples")
    op.drop_table("api_keys")
    op.drop_table("voice_profiles")
    op.execute("DROP TYPE IF EXISTS voicestatus")
    op.execute("DROP TYPE IF EXISTS trainingmode")
    op.execute("DROP TYPE IF EXISTS jobstatus")
