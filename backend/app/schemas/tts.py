from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = "en"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch_semitones: float = Field(default=0.0, ge=-12.0, le=12.0)
    format: str = Field(default="wav", pattern="^(wav|mp3)$")
