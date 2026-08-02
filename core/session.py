import json
import secrets
import base64
from pathlib import Path
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet

SESSION_FILE = Path(__file__).parent.parent / ".nullvault_storage" / ".session"
SESSION_TTL_MINUTES = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def save_session(token: str, username: str, user_id: int, fernet_key: bytes):
    """
    Persist session to disk. The user's fernet key is wrapped with a
    randomly-generated session key so it is never stored in plaintext.
    The session key itself is stored alongside — this protects against
    casual inspection but the real security boundary is the encrypted vault.
    """
    session_key = Fernet.generate_key()
    wrapped_key = Fernet(session_key).encrypt(fernet_key)
    expires = _now() + timedelta(minutes=SESSION_TTL_MINUTES)

    data = {
        "token": token,
        "username": username,
        "user_id": user_id,
        "expires_at": expires.isoformat(),
        "session_key": session_key.decode(),
        "wrapped_key": base64.b64encode(wrapped_key).decode(),
    }
    SESSION_FILE.parent.mkdir(exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data))


def load_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text())
        expires = datetime.fromisoformat(data["expires_at"])
        if _now() > expires:
            clear_session()
            return None
        # Unwrap the fernet key back into bytes
        session_key = data["session_key"].encode()
        wrapped_key = base64.b64decode(data["wrapped_key"])
        data["fernet_key"] = Fernet(session_key).decrypt(wrapped_key)
        return data
    except Exception:
        clear_session()
        return None


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def refresh_session(token: str, username: str, user_id: int, fernet_key: bytes):
    save_session(token, username, user_id, fernet_key)
