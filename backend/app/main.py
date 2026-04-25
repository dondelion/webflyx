from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.api import voices, samples, chunks, training, tts, auth as auth_router
from app.api.public import router as public_router

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="WebFlyx Voice",
    description="Voice cloning platform — upload samples, train voices, synthesize speech.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Internal management API
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(voices.router, prefix="/api/voices", tags=["voices"])
app.include_router(samples.router, prefix="/api/voices", tags=["samples"])
app.include_router(chunks.router, prefix="/api/voices", tags=["chunks"])
app.include_router(training.router, prefix="/api/voices", tags=["training"])
app.include_router(tts.router, prefix="/api/voices", tags=["tts"])

# Public API
app.include_router(public_router, prefix="/v1", tags=["public"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
