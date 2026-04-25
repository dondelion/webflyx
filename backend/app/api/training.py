import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.voice_profile import VoiceProfile
from app.models.training_job import TrainingJob, JobStatus
from app.schemas.training import TrainingJobCreate, TrainingJobOut

router = APIRouter()


@router.post("/{voice_id}/train", response_model=TrainingJobOut, status_code=status.HTTP_202_ACCEPTED)
async def start_training(
    voice_id: uuid.UUID,
    body: TrainingJobCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    job = TrainingJob(voice_id=voice_id, mode=body.mode, status=JobStatus.queued)
    db.add(job)
    await db.flush()
    await db.refresh(job)

    chunk_ids = [str(cid) for cid in body.chunk_ids] if body.chunk_ids else []
    from app.tasks.training import run_voice_training
    task = run_voice_training.delay(str(voice_id), str(job.id), chunk_ids, body.mode.value)
    job.celery_task_id = task.id
    await db.flush()
    await db.refresh(job)

    return job


@router.get("/{voice_id}/training-jobs", response_model=list[TrainingJobOut])
async def list_training_jobs(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingJob)
        .where(TrainingJob.voice_id == voice_id)
        .order_by(TrainingJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{voice_id}/training-jobs/{job_id}", response_model=TrainingJobOut)
async def get_training_job(
    voice_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TrainingJob).where(
            TrainingJob.id == job_id, TrainingJob.voice_id == voice_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


@router.delete("/{voice_id}/training-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_training_job(
    voice_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TrainingJob).where(
            TrainingJob.id == job_id, TrainingJob.voice_id == voice_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")

    if job.celery_task_id:
        from app.tasks import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = JobStatus.cancelled
    await db.flush()
