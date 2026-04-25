import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.audio_sample import AudioSample
from app.models.audio_chunk import AudioChunk
from app.schemas.chunk import ChunkCreate, ChunkUpdate, ChunkOut
from app.schemas.phoneme import CoverageReport
from app.services.phoneme import PhonemeService

router = APIRouter()


@router.post(
    "/{voice_id}/samples/{sample_id}/chunks",
    response_model=ChunkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_chunk(
    voice_id: uuid.UUID,
    sample_id: uuid.UUID,
    body: ChunkCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AudioSample).where(
            AudioSample.id == sample_id, AudioSample.voice_id == voice_id
        )
    )
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    if body.start_sec >= body.end_sec:
        raise HTTPException(status_code=400, detail="start_sec must be less than end_sec")

    chunk = AudioChunk(
        sample_id=sample_id,
        start_sec=body.start_sec,
        end_sec=body.end_sec,
        transcript=body.transcript,
        selected=body.selected,
    )
    db.add(chunk)
    await db.flush()
    await db.refresh(chunk)

    if body.transcript:
        from app.tasks.phonemize import run_phonemize_chunk
        run_phonemize_chunk.delay(str(chunk.id))

    return chunk


@router.get("/{voice_id}/samples/{sample_id}/chunks", response_model=list[ChunkOut])
async def list_chunks_for_sample(
    voice_id: uuid.UUID,
    sample_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AudioSample).where(
            AudioSample.id == sample_id, AudioSample.voice_id == voice_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Sample not found")

    result = await db.execute(
        select(AudioChunk)
        .where(AudioChunk.sample_id == sample_id)
        .order_by(AudioChunk.start_sec)
    )
    return result.scalars().all()


@router.get("/{voice_id}/chunks", response_model=list[ChunkOut])
async def list_all_chunks(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AudioChunk)
        .join(AudioSample, AudioChunk.sample_id == AudioSample.id)
        .where(AudioSample.voice_id == voice_id)
        .order_by(AudioChunk.start_sec)
    )
    return result.scalars().all()


@router.patch("/{voice_id}/chunks/{chunk_id}", response_model=ChunkOut)
async def update_chunk(
    voice_id: uuid.UUID,
    chunk_id: uuid.UUID,
    body: ChunkUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AudioChunk)
        .join(AudioSample, AudioChunk.sample_id == AudioSample.id)
        .where(AudioChunk.id == chunk_id, AudioSample.voice_id == voice_id)
    )
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    transcript_changed = body.transcript is not None and body.transcript != chunk.transcript

    if body.transcript is not None:
        chunk.transcript = body.transcript
        chunk.phonemes = None
    if body.selected is not None:
        chunk.selected = body.selected

    await db.flush()
    await db.refresh(chunk)

    if transcript_changed and chunk.transcript:
        from app.tasks.phonemize import run_phonemize_chunk
        run_phonemize_chunk.delay(str(chunk.id))

    return chunk


@router.delete("/{voice_id}/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chunk(
    voice_id: uuid.UUID,
    chunk_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AudioChunk)
        .join(AudioSample, AudioChunk.sample_id == AudioSample.id)
        .where(AudioChunk.id == chunk_id, AudioSample.voice_id == voice_id)
    )
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    await db.delete(chunk)


@router.post("/{voice_id}/chunks/{chunk_id}/transcribe", status_code=status.HTTP_202_ACCEPTED)
async def auto_transcribe_chunk(
    voice_id: uuid.UUID,
    chunk_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AudioChunk)
        .join(AudioSample, AudioChunk.sample_id == AudioSample.id)
        .where(AudioChunk.id == chunk_id, AudioSample.voice_id == voice_id)
    )
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    chunk.transcription_pending = True
    await db.flush()

    from app.tasks.transcribe import run_whisper_transcription
    task = run_whisper_transcription.delay(str(chunk_id))
    return {"task_id": task.id, "status": "queued"}


@router.get("/{voice_id}/coverage", response_model=CoverageReport)
async def get_coverage(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = PhonemeService()
    return await service.analyze_coverage(voice_id, db)
