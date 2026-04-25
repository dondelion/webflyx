import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.storage import get_storage
from app.models.voice_profile import VoiceProfile
from app.models.audio_sample import AudioSample
from app.schemas.sample import SampleOut
from app.services.audio import AudioService

router = APIRouter()


async def _get_voice_or_404(voice_id: uuid.UUID, db: AsyncSession) -> VoiceProfile:
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.post("/{voice_id}/samples", response_model=SampleOut, status_code=status.HTTP_201_CREATED)
async def upload_sample(
    voice_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    await _get_voice_or_404(voice_id, db)
    audio_service = AudioService(get_storage())
    sample = await audio_service.ingest_upload(voice_id, file, db)
    return sample


@router.get("/{voice_id}/samples", response_model=list[SampleOut])
async def list_samples(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _get_voice_or_404(voice_id, db)
    result = await db.execute(
        select(AudioSample)
        .where(AudioSample.voice_id == voice_id)
        .order_by(AudioSample.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{voice_id}/samples/{sample_id}", response_model=SampleOut)
async def get_sample(
    voice_id: uuid.UUID, sample_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AudioSample).where(
            AudioSample.id == sample_id, AudioSample.voice_id == voice_id
        )
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample


@router.get("/{voice_id}/samples/{sample_id}/waveform")
async def get_waveform(
    voice_id: uuid.UUID, sample_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AudioSample).where(
            AudioSample.id == sample_id, AudioSample.voice_id == voice_id
        )
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    audio_service = AudioService(get_storage())
    waveform_data = audio_service.generate_waveform_data(sample.storage_path)
    return {"data": waveform_data, "duration": sample.duration_sec}


@router.get("/{voice_id}/samples/{sample_id}/stream")
async def stream_sample(
    voice_id: uuid.UUID, sample_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AudioSample).where(
            AudioSample.id == sample_id, AudioSample.voice_id == voice_id
        )
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    storage = get_storage()
    abs_path = storage.get_abs_path(sample.storage_path)

    media_type = "audio/wav" if sample.format == "wav" else "audio/mpeg"
    return FileResponse(abs_path, media_type=media_type, filename=sample.original_filename)


@router.delete("/{voice_id}/samples/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sample(
    voice_id: uuid.UUID, sample_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AudioSample).where(
            AudioSample.id == sample_id, AudioSample.voice_id == voice_id
        )
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    storage = get_storage()
    try:
        storage.delete(sample.storage_path)
    except Exception:
        pass

    await db.delete(sample)
