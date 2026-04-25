import uuid
from app.tasks import celery_app


@celery_app.task(name="tasks.run_phonemize_chunk")
def run_phonemize_chunk(chunk_id: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.models.audio_chunk import AudioChunk
    from app.services.phoneme import extract_phonemes_from_text

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        chunk = db.get(AudioChunk, uuid.UUID(chunk_id))
        if not chunk or not chunk.transcript:
            return

        phonemes = extract_phonemes_from_text(chunk.transcript)
        chunk.phonemes = phonemes
        db.commit()
