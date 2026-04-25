import uuid
from datetime import datetime, timezone
from celery import Task
from app.tasks import celery_app


@celery_app.task(bind=True, name="tasks.run_voice_training")
def run_voice_training(
    self: Task,
    voice_id: str,
    job_id: str,
    chunk_ids: list[str],
    mode: str,
):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.core.storage import get_storage
    from app.models.training_job import TrainingJob, JobStatus
    from app.models.voice_profile import VoiceProfile, VoiceStatus
    from app.models.audio_chunk import AudioChunk
    from app.models.audio_sample import AudioSample
    from app.models.voice_embedding import VoiceEmbedding
    from app.services.trainer import VoiceTrainer
    from app.services.audio import AudioService

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        job = db.get(TrainingJob, uuid.UUID(job_id))
        if not job:
            return

        job.status = JobStatus.running
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        try:
            self.update_state(state="PROGRESS", meta={"progress": 5})

            # Determine which chunks to use
            if chunk_ids:
                chunks = db.query(AudioChunk).filter(
                    AudioChunk.id.in_([uuid.UUID(cid) for cid in chunk_ids])
                ).all()
            else:
                # Use all selected chunks for this voice
                chunks = (
                    db.query(AudioChunk)
                    .join(AudioSample, AudioChunk.sample_id == AudioSample.id)
                    .filter(
                        AudioSample.voice_id == uuid.UUID(voice_id),
                        AudioChunk.selected == True,
                    )
                    .all()
                )

            if not chunks:
                raise ValueError("No chunks selected for training")

            storage = get_storage()
            audio_service = AudioService(storage)
            trainer = VoiceTrainer(storage)

            # Export chunks to individual WAV files
            self.update_state(state="PROGRESS", meta={"progress": 20})
            export_paths = []
            for chunk in chunks:
                sample = db.get(AudioSample, chunk.sample_id)
                out_path = storage.get_abs_path(
                    f"voices/{voice_id}/tmp/{chunk.id}.wav"
                )
                audio_service.export_chunk(
                    sample.storage_path, chunk.start_sec, chunk.end_sec, out_path
                )
                audio_service.normalize_chunk(out_path)
                export_paths.append(out_path)

            self.update_state(state="PROGRESS", meta={"progress": 40})

            if mode == "zero_shot":
                result = trainer.extract_voice_embedding(
                    uuid.UUID(voice_id), export_paths, None, uuid.UUID(job_id)
                )
                self.update_state(state="PROGRESS", meta={"progress": 80})

                existing_emb = (
                    db.query(VoiceEmbedding)
                    .filter(VoiceEmbedding.voice_id == uuid.UUID(voice_id))
                    .first()
                )
                if existing_emb:
                    existing_emb.gpt_cond_latent_path = result["gpt_cond_latent_path"]
                    existing_emb.speaker_embedding_path = result["speaker_embedding_path"]
                    existing_emb.reference_audio_path = result.get("reference_audio_path")
                else:
                    emb = VoiceEmbedding(
                        voice_id=uuid.UUID(voice_id),
                        gpt_cond_latent_path=result["gpt_cond_latent_path"],
                        speaker_embedding_path=result["speaker_embedding_path"],
                        reference_audio_path=result.get("reference_audio_path"),
                    )
                    db.add(emb)

                job.model_path = result["speaker_embedding_path"]

            else:  # finetune
                chunk_dicts = []
                for chunk in chunks:
                    sample = db.get(AudioSample, chunk.sample_id)
                    chunk_dicts.append({
                        "id": str(chunk.id),
                        "storage_path": sample.storage_path,
                        "start_sec": chunk.start_sec,
                        "end_sec": chunk.end_sec,
                        "transcript": chunk.transcript,
                    })

                self.update_state(state="PROGRESS", meta={"progress": 50})
                dataset_path = trainer.prepare_finetune_dataset(
                    uuid.UUID(voice_id), chunk_dicts
                )

                self.update_state(state="PROGRESS", meta={"progress": 60})
                model_dir = trainer.finetune(uuid.UUID(voice_id), dataset_path)
                job.model_path = model_dir

            job.status = JobStatus.completed
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)

            voice = db.get(VoiceProfile, uuid.UUID(voice_id))
            if voice:
                voice.status = VoiceStatus.ready

            db.commit()

        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)

            voice = db.get(VoiceProfile, uuid.UUID(voice_id))
            if voice:
                voice.status = VoiceStatus.failed

            db.commit()
            raise
