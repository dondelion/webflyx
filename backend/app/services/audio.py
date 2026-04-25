import os
import uuid
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.storage import LocalStorageBackend

ALLOWED_AUDIO = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
ALLOWED_VIDEO = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


class AudioService:
    def __init__(self, storage: "LocalStorageBackend"):
        self.storage = storage

    async def ingest_upload(self, voice_id: uuid.UUID, file, db) -> "AudioSample":  # noqa: F821
        from app.models.audio_sample import AudioSample

        content = await file.read()
        ext = Path(file.filename).suffix.lower()

        if ext not in ALLOWED_AUDIO and ext not in ALLOWED_VIDEO:
            raise ValueError(f"Unsupported file type: {ext}")

        stored_name = f"{uuid.uuid4()}{ext}"
        rel_path = f"voices/{voice_id}/samples/{stored_name}"
        abs_path = self.storage.save(rel_path, content)

        if ext in ALLOWED_VIDEO:
            wav_name = stored_name.replace(ext, ".wav")
            wav_rel = f"voices/{voice_id}/samples/{wav_name}"
            wav_abs = self.storage.get_abs_path(wav_rel)
            self._extract_audio_from_video(abs_path, wav_abs)
            rel_path = wav_rel
            abs_path = wav_abs
            ext = ".wav"

        elif ext != ".wav":
            wav_name = stored_name.replace(ext, ".wav")
            wav_rel = f"voices/{voice_id}/samples/{wav_name}"
            wav_abs = self.storage.get_abs_path(wav_rel)
            self._convert_to_wav(abs_path, wav_abs)
            rel_path = wav_rel
            abs_path = wav_abs
            ext = ".wav"

        meta = self._get_audio_metadata(abs_path)

        sample = AudioSample(
            voice_id=voice_id,
            original_filename=file.filename,
            stored_filename=Path(rel_path).name,
            storage_path=rel_path,
            duration_sec=meta.get("duration"),
            sample_rate=meta.get("sample_rate"),
            channels=meta.get("channels"),
            format="wav",
        )
        db.add(sample)
        await db.flush()
        await db.refresh(sample)
        return sample

    def _extract_audio_from_video(self, video_path: str, out_wav: str) -> None:
        os.makedirs(os.path.dirname(out_wav), exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
                out_wav,
            ],
            check=True,
            capture_output=True,
        )

    def _convert_to_wav(self, src: str, out_wav: str) -> None:
        os.makedirs(os.path.dirname(out_wav), exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", src,
                "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
                out_wav,
            ],
            check=True,
            capture_output=True,
        )

    def _get_audio_metadata(self, path: str) -> dict:
        try:
            import soundfile as sf
            info = sf.info(path)
            return {
                "duration": info.duration,
                "sample_rate": info.samplerate,
                "channels": info.channels,
            }
        except Exception:
            return {}

    def generate_waveform_data(self, storage_path: str, num_points: int = 1000) -> list[float]:
        try:
            import numpy as np
            import soundfile as sf

            abs_path = self.storage.get_abs_path(storage_path)
            data, sr = sf.read(abs_path, dtype="float32", always_2d=False)

            if data.ndim > 1:
                data = data.mean(axis=1)

            chunk_size = max(1, len(data) // num_points)
            peaks = []
            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                peaks.append(float(np.abs(chunk).max()))

            return peaks[:num_points]
        except Exception:
            return []

    def export_chunk(
        self, storage_path: str, start_sec: float, end_sec: float, out_path: str
    ) -> None:
        from pydub import AudioSegment

        abs_path = self.storage.get_abs_path(storage_path)
        audio = AudioSegment.from_wav(abs_path)
        chunk = audio[int(start_sec * 1000) : int(end_sec * 1000)]
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        chunk.export(out_path, format="wav")

    def normalize_chunk(self, wav_path: str) -> str:
        try:
            import soundfile as sf
            import pyloudnorm as pyln
            import numpy as np

            data, rate = sf.read(wav_path)
            meter = pyln.Meter(rate)
            loudness = meter.integrated_loudness(data)
            normalized = pyln.normalize.loudness(data, loudness, -23.0)
            sf.write(wav_path, normalized, rate)
        except Exception:
            pass
        return wav_path

    def concatenate_chunks(self, wav_paths: list[str], out_path: str) -> None:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for p in wav_paths:
            combined += AudioSegment.from_wav(p)
        combined.export(out_path, format="wav")
