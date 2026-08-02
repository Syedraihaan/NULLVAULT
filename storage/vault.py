import io
import secrets
import zipfile
from pathlib import Path

from crypto.engine import encrypt_data, decrypt_data
from database import db
from utils.helpers import (
    sha256_bytes, compress, decompress,
    safe_filename, utcnow_iso, CHUNK_SIZE,
)
from logs.logger import log_info, log_error

VAULT_ROOT = Path(__file__).parent.parent / ".nullvault_storage" / "files"


def _user_dir(user_id: int) -> Path:
    d = VAULT_ROOT / str(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _new_hash_id() -> str:
    return secrets.token_hex(16)


def _clean_path(p: str) -> str:
    return p.strip().strip('"').strip("'")


def _zip_directory(src: Path) -> bytes:
    """Zip an entire directory tree into an in-memory bytes blob."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for file in src.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(src.parent))
    return buf.getvalue()


def _encrypt_blob(raw_data: bytes, fernet_key: bytes) -> bytes:
    return encrypt_data(compress(raw_data), fernet_key)


def _decrypt_blob(ciphertext: bytes, fernet_key: bytes) -> bytes:
    return decompress(decrypt_data(ciphertext, fernet_key))


def store(user_id: int, src_path: str, fernet_key: bytes) -> str:
    """
    Store a file OR directory. Returns hash_id.
    - File  -> read raw bytes -> compress -> encrypt -> store
    - Dir   -> zip entire tree -> compress -> encrypt -> store
    """
    src_path = _clean_path(src_path)
    src = Path(src_path)

    if not src.exists():
        raise FileNotFoundError(f"Path does not exist: {src_path}")

    if src.is_dir():
        orig_name = src.name
        raw_data = _zip_directory(src)
        entry_type = "dir"
        original_size = sum(f.stat().st_size for f in src.rglob("*") if f.is_file())
    else:
        orig_name = safe_filename(src.name)
        raw_chunks = []
        with open(src, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                raw_chunks.append(chunk)
        raw_data = b"".join(raw_chunks)
        entry_type = "file"
        original_size = src.stat().st_size

    src_sha256 = sha256_bytes(raw_data)
    ciphertext = _encrypt_blob(raw_data, fernet_key)

    hash_id = _new_hash_id()
    (_user_dir(user_id) / hash_id).write_bytes(ciphertext)

    db.insert_file(user_id, hash_id, orig_name, original_size, src_sha256, utcnow_iso(), entry_type)
    log_info("stored", user_id=user_id, hash_id=hash_id, name=orig_name, type=entry_type)
    return hash_id


def retrieve(user_id: int, hash_id: str, dest_dir: str, fernet_key: bytes) -> str:
    """
    Retrieve a file or directory from the vault.
    - file -> writes single file to dest_dir
    - dir  -> extracts zip into dest_dir, restoring full folder structure
    Returns the output path.
    """
    record = db.get_file(user_id, hash_id)
    if not record:
        raise FileNotFoundError(f"No entry with ID '{hash_id}' in your vault.")

    vault_path = _user_dir(user_id) / hash_id
    if not vault_path.exists():
        raise FileNotFoundError("Vault blob missing — possible tampering detected.")

    raw_data = _decrypt_blob(vault_path.read_bytes(), fernet_key)

    if sha256_bytes(raw_data) != record["sha256"]:
        log_error("integrity_failure", user_id=user_id, hash_id=hash_id)
        raise ValueError("Integrity check FAILED. Data may be corrupted or tampered.")

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if record["entry_type"] == "dir":
        with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
            zf.extractall(dest)
        out_path = str(dest / record["orig_name"])
    else:
        out_path = str(dest / safe_filename(record["orig_name"]))
        Path(out_path).write_bytes(raw_data)

    log_info("retrieved", user_id=user_id, hash_id=hash_id, dest=out_path)
    return out_path


def list_entries(user_id: int) -> list:
    return db.list_files(user_id)


def delete_entry(user_id: int, hash_id: str):
    record = db.get_file(user_id, hash_id)
    if not record:
        raise FileNotFoundError(f"No entry with ID '{hash_id}'.")

    vault_path = _user_dir(user_id) / hash_id
    if vault_path.exists():
        vault_path.unlink()

    db.delete_file_record(user_id, hash_id)
    log_info("deleted", user_id=user_id, hash_id=hash_id)
