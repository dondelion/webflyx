from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import generate_api_key, hash_key
from app.models.api_key import APIKey
from app.schemas.auth import APIKeyCreate, APIKeyOut, APIKeyCreated

router = APIRouter()


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(body: APIKeyCreate, db: AsyncSession = Depends(get_db)):
    raw_key = generate_api_key()
    key = APIKey(
        name=body.name,
        voice_id=body.voice_id,
        key_hash=hash_key(raw_key),
    )
    db.add(key)
    await db.flush()
    await db.refresh(key)
    return APIKeyCreated(
        id=key.id,
        name=key.name,
        voice_id=key.voice_id,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
        raw_key=raw_key,
    )


@router.get("", response_model=list[APIKeyOut])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    return result.scalars().all()


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(key)
