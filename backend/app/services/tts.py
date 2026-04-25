import io
from typing import Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.voice_embedding import VoiceEmbedding


class TTSService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tts = None
        return cls._instance

    @property
    def tts(self):
        if self._tts is None:
            try:
                import torch
                from TTS.api import TTS
                self._tts = TTS(
                    "tts_models/multilingual/multi-dataset/xtts_v2",
                    gpu=torch.cuda.is_available(),
                )
            except ImportError:
                raise RuntimeError(
                    "Coqui TTS not installed. Install with: pip install TTS torch torchaudio"
                )
        return self._tts

    def _load_latents(self, embedding: "VoiceEmbedding"):
        import torch
        from app.core.storage import get_storage

        storage = get_storage()
        gpt_path = storage.get_abs_path(embedding.gpt_cond_latent_path)
        spk_path = storage.get_abs_path(embedding.speaker_embedding_path)

        gpt_cond_latent = torch.load(gpt_path, map_location="cpu")
        speaker_embedding = torch.load(spk_path, map_location="cpu")
        return gpt_cond_latent, speaker_embedding

    def synthesize_stream(
        self, text: str, embedding: "VoiceEmbedding"
    ) -> Generator[bytes, None, None]:
        import numpy as np
        import soundfile as sf

        gpt_cond_latent, speaker_embedding = self._load_latents(embedding)

        chunks = self.tts.inference_stream(
            text,
            language="en",
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
        )

        buf = io.BytesIO()
        with sf.SoundFile(buf, mode="w", samplerate=24000, channels=1, format="WAV") as f:
            for chunk in chunks:
                if isinstance(chunk, list):
                    chunk = np.array(chunk)
                f.write(chunk)

        buf.seek(0)
        yield buf.read()

    def synthesize_full(
        self,
        text: str,
        embedding: "VoiceEmbedding",
        speed: float = 1.0,
        pitch_semitones: float = 0.0,
    ) -> bytes:
        import numpy as np
        import soundfile as sf
        import io

        gpt_cond_latent, speaker_embedding = self._load_latents(embedding)

        output = self.tts.inference(
            text,
            language="en",
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
        )

        audio = np.array(output["wav"])
        sr = output.get("sample_rate", 24000)

        if speed != 1.0:
            import librosa
            audio = librosa.effects.time_stretch(audio, rate=speed)

        if pitch_semitones != 0.0:
            import librosa
            audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch_semitones)

        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV")
        buf.seek(0)
        return buf.read()
