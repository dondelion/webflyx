import os
import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable
from app.core.config import get_settings

settings = get_settings()


@runtime_checkable
class StorageBackend(Protocol):
    def save(self, relative_path: str, data: bytes) -> str: ...
    def load(self, relative_path: str) -> bytes: ...
    def delete(self, relative_path: str) -> None: ...
    def get_abs_path(self, relative_path: str) -> str: ...
    def ensure_dir(self, relative_dir: str) -> str: ...


class LocalStorageBackend:
    def __init__(self, base_path: str):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, relative_path: str, data: bytes) -> str:
        abs_path = self.base / relative_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(data)
        return str(abs_path)

    def load(self, relative_path: str) -> bytes:
        return (self.base / relative_path).read_bytes()

    def delete(self, relative_path: str) -> None:
        p = self.base / relative_path
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def get_abs_path(self, relative_path: str) -> str:
        return str(self.base / relative_path)

    def ensure_dir(self, relative_dir: str) -> str:
        d = self.base / relative_dir
        d.mkdir(parents=True, exist_ok=True)
        return str(d)


_storage: LocalStorageBackend | None = None


def get_storage() -> LocalStorageBackend:
    global _storage
    if _storage is None:
        _storage = LocalStorageBackend(settings.storage_path)
    return _storage
