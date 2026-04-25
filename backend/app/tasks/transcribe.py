import uuid
from app.tasks import celery_app


@celery_app.task(bind=True, name="tasks.run_whisper_transcription")
def run_whisper_transcription(self, chunk_id: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.core.storage import get_storage
    from app.models.audio_chunk import AudioChunk
    from app.models.audio_sample import AudioSample
    from app.services.audio import AudioService
    from app.services.phoneme import extract_phonemes_from_text

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        chunk = db.get(AudioChunk, uuid.UUID(chunk_id))
        if not chunk:
            return

        sample = db.get(AudioSample, chunk.sample_id)
        if not sample:
            return

        storage = get_storage()
        audio_service = AudioService(storage)

        out_path = storage.get_abs_path(f"tmp/transcribe_{chunk_id}.wav")
        audio_service.export_chunk(
            sample.storage_path, chunk.start_sec, chunk.end_sec, out_path
        )

        try:
            import whisper
            model = whisper.load_model("base.en")
            result = model.transcribe(out_path)
            transcript = result["text"].strip()

            chunk.transcript = transcript
            chunk.phonemes = extract_phonemes_from_text(transcript)
            chunk.transcription_pending = False
            db.commit()

        except Exception as exc:
            chunk.transcription_pending = False
            db.commit()
            raise

        finally:
            import os
            if os.path.exists(out_path):
                os.unlink(out_path)
