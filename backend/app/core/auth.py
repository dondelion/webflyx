import hashlib
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> str:
    return "wfv_" + secrets.token_urlsafe(32)


async def get_api_key(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = None,
):
    from app.models.api_key import APIKey

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )

    key_hash = hash_key(api_key)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    key_record = result.scalar_one_or_none()

    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return key_record
