import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.storage import LocalStorageBackend


class VoiceTrainer:
    def __init__(self, storage: "LocalStorageBackend"):
        self.storage = storage

    def extract_voice_embedding(
        self,
        voice_id: uuid.UUID,
        chunk_export_paths: list[str],
        db_session_factory,
        job_id: uuid.UUID,
    ) -> dict:
        import torch

        ref_audio = self.storage.get_abs_path(f"voices/{voice_id}/ref_audio.wav")
        self._concatenate_wavs(chunk_export_paths, ref_audio)

        tts = self._load_xtts()
        gpt_cond_latent, speaker_embedding = tts.get_conditioning_latents(
            audio_path=[ref_audio]
        )

        embedding_dir = self.storage.ensure_dir(f"voices/{voice_id}/embeddings")
        gpt_path = os.path.join(embedding_dir, "gpt_cond_latent.pt")
        spk_path = os.path.join(embedding_dir, "speaker_embedding.pt")

        torch.save(gpt_cond_latent, gpt_path)
        torch.save(speaker_embedding, spk_path)

        return {
            "gpt_cond_latent_path": f"voices/{voice_id}/embeddings/gpt_cond_latent.pt",
            "speaker_embedding_path": f"voices/{voice_id}/embeddings/speaker_embedding.pt",
            "reference_audio_path": f"voices/{voice_id}/ref_audio.wav",
        }

    def prepare_finetune_dataset(
        self, voice_id: uuid.UUID, chunks: list[dict]
    ) -> str:
        dataset_dir = self.storage.ensure_dir(f"voices/{voice_id}/dataset/wavs")
        dataset_base = self.storage.get_abs_path(f"voices/{voice_id}/dataset")
        metadata_lines = []

        for chunk in chunks:
            out_path = os.path.join(dataset_dir, f"{chunk['id']}.wav")
            if not os.path.exists(out_path):
                from app.services.audio import AudioService
                audio_service = AudioService(self.storage)
                audio_service.export_chunk(
                    chunk["storage_path"],
                    chunk["start_sec"],
                    chunk["end_sec"],
                    out_path,
                )
                audio_service.normalize_chunk(out_path)

            if chunk.get("transcript"):
                metadata_lines.append(f"wavs/{chunk['id']}.wav|{chunk['transcript']}")

        metadata_path = os.path.join(dataset_base, "metadata.csv")
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write("\n".join(metadata_lines))

        return dataset_base

    def finetune(
        self,
        voice_id: uuid.UUID,
        dataset_path: str,
        progress_callback=None,
    ) -> str:
        import yaml

        output_dir = self.storage.ensure_dir(f"voices/{voice_id}/checkpoints")
        config = self._build_finetune_config(str(voice_id), dataset_path, output_dir)

        config_path = os.path.join(output_dir, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        try:
            from TTS.bin.train_tts import main as tts_train
            tts_train(config_path)
        except ImportError:
            raise RuntimeError(
                "Coqui TTS not installed. Install with: pip install TTS"
            )

        return output_dir

    def _build_finetune_config(
        self, voice_id: str, dataset_path: str, output_dir: str
    ) -> dict:
        return {
            "model": "xtts",
            "run_name": f"voice_{voice_id}",
            "audio": {"sample_rate": 22050, "win_length": 1024, "hop_length": 256},
            "datasets": [
                {
                    "name": "custom",
                    "path": dataset_path,
                    "meta_file_train": "metadata.csv",
                    "language": "en",
                }
            ],
            "trainer": {
                "epochs": 10,
                "batch_size": 2,
                "gradient_accumulation_steps": 4,
                "learning_rate": 5.0e-6,
                "optimizer": "AdamW",
            },
            "mixed_precision": True,
            "save_step": 5000,
            "output_path": output_dir,
        }

    def _load_xtts(self):
        try:
            import torch
            from TTS.api import TTS
            return TTS(
                "tts_models/multilingual/multi-dataset/xtts_v2",
                gpu=torch.cuda.is_available(),
            )
        except ImportError:
            raise RuntimeError(
                "Coqui TTS not installed. Install with: pip install TTS torch torchaudio"
            )

    def _concatenate_wavs(self, wav_paths: list[str], out_path: str) -> None:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for p in wav_paths:
            if os.path.exists(p):
                combined += AudioSegment.from_wav(p)

        if len(combined) == 0:
            raise ValueError("No valid audio found in provided chunk paths")

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        combined.export(out_path, format="wav")
