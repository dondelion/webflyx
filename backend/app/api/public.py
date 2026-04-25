import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.models.voice_profile import VoiceProfile, VoiceStatus
from app.models.voice_embedding import VoiceEmbedding
from app.schemas.voice import VoiceOut
from app.schemas.tts import TTSRequest

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health")
async def public_health():
    return {"status": "ok", "service": "webflyx-voice"}


@router.get("/voices", response_model=list[VoiceOut])
async def public_list_voices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VoiceProfile)
        .where(VoiceProfile.status == VoiceStatus.ready)
        .order_by(VoiceProfile.name)
    )
    return result.scalars().all()


@router.get("/voices/{voice_id}", response_model=VoiceOut)
async def public_get_voice(voice_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VoiceProfile).where(
            VoiceProfile.id == voice_id, VoiceProfile.status == VoiceStatus.ready
        )
    )
    voice = result.scalar_one_or_none()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.post("/voices/{voice_id}/tts")
@limiter.limit("100/minute")
async def public_synthesize(
    request: Request,
    voice_id: uuid.UUID,
    body: TTSRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VoiceEmbedding).where(VoiceEmbedding.voice_id == voice_id)
    )
    embedding = result.scalar_one_or_none()
    if not embedding:
        raise HTTPException(status_code=404, detail="Voice not trained")

    from app.services.tts import TTSService
    tts_service = TTSService()

    needs_postprocess = body.speed != 1.0 or body.pitch_semitones != 0.0

    if needs_postprocess:
        audio_bytes = tts_service.synthesize_full(body.text, embedding, body.speed, body.pitch_semitones)
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/wav",
            headers={
                "X-Voice-Id": str(voice_id),
                "Content-Disposition": "inline; filename=synthesis.wav",
            },
        )
    else:
        return StreamingResponse(
            tts_service.synthesize_stream(body.text, embedding),
            media_type="audio/wav",
            headers={
                "X-Voice-Id": str(voice_id),
                "Content-Disposition": "inline; filename=synthesis.wav",
            },
        )
