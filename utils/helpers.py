import os
import json
import zlib
import hashlib
import secrets
import shutil
from pathlib import Path
from datetime import datetime, timezone

CHUNK_SIZE = 1024 * 1024  # 1MB chunks


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_token(length: int = 32) -> str:
    return secrets.token_hex(length)


def safe_filename(name: str) -> str:
    """Strip path traversal attempts from a filename."""
    return Path(name).name


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compress(data: bytes) -> bytes:
    return zlib.compress(data, level=6)


def decompress(data: bytes) -> bytes:
    return zlib.decompress(data)
