import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.voice_embedding import VoiceEmbedding
from app.schemas.tts import TTSRequest

router = APIRouter()


@router.post("/{voice_id}/synthesize")
async def synthesize(
    voice_id: uuid.UUID,
    body: TTSRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VoiceEmbedding).where(VoiceEmbedding.voice_id == voice_id)
    )
    embedding = result.scalar_one_or_none()
    if not embedding:
        raise HTTPException(
            status_code=404,
            detail="Voice not trained yet. Run training first.",
        )

    from app.services.tts import TTSService
    tts_service = TTSService()

    needs_postprocess = body.speed != 1.0 or body.pitch_semitones != 0.0

    if needs_postprocess:
        audio_bytes = tts_service.synthesize_full(body.text, embedding, body.speed, body.pitch_semitones)
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=synthesis.wav"},
        )
    else:
        return StreamingResponse(
            tts_service.synthesize_stream(body.text, embedding),
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=synthesis.wav"},
        )
