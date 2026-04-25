import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.voice_profile import VoiceProfile
from app.schemas.voice import VoiceCreate, VoiceUpdate, VoiceOut

router = APIRouter()


@router.post("", response_model=VoiceOut, status_code=status.HTTP_201_CREATED)
async def create_voice(body: VoiceCreate, db: AsyncSession = Depends(get_db)):
    voice = VoiceProfile(name=body.name, description=body.description)
    db.add(voice)
    await db.flush()
    await db.refresh(voice)
    return voice


@router.get("", response_model=list[VoiceOut])
async def list_voices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VoiceProfile).order_by(VoiceProfile.created_at.desc()))
    return result.scalars().all()


@router.get("/{voice_id}", response_model=VoiceOut)
async def get_voice(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.patch("/{voice_id}", response_model=VoiceOut)
async def update_voice(
    voice_id: uuid.UUID, body: VoiceUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    if body.name is not None:
        voice.name = body.name
    if body.description is not None:
        voice.description = body.description
    await db.flush()
    await db.refresh(voice)
    return voice


@router.delete("/{voice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VoiceProfile).where(VoiceProfile.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    await db.delete(voice)
