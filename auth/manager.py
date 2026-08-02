import bcrypt
from datetime import datetime, timezone, timedelta

from database import db
from crypto.engine import generate_user_key, encrypt_user_key, decrypt_user_key
from core.session import save_session, clear_session
from core.decoy import provision_decoy
from utils.helpers import generate_token, utcnow_iso
from logs.logger import log_info, log_warning, log_error

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def register(username: str, password: str) -> str:
    if db.get_user(username):
        raise ValueError(f"User '{username}' already exists.")

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    raw_key = generate_user_key()
    enc_key = encrypt_user_key(raw_key, password)

    db.create_user(username, pw_hash, enc_key, utcnow_iso())
    provision_decoy(username, password)
    log_info("user_registered", username=username)
    return f"User '{username}' registered successfully."


def login(username: str, password: str) -> tuple[str, bytes]:
    """Returns (session_token, raw_fernet_key)."""
    since = (_utcnow() - timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
    failed = db.recent_failed_attempts(username, since)

    if failed >= MAX_ATTEMPTS:
        log_warning("brute_force_lockout", username=username)
        raise PermissionError("Account temporarily locked. Try again later.")

    user = db.get_user(username)

    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        db.record_attempt(username, False, utcnow_iso())
        log_warning("login_failed", username=username)
        raise PermissionError("Invalid credentials.")

    db.record_attempt(username, True, utcnow_iso())

    # Decrypt the user's Fernet key
    raw_key = decrypt_user_key(bytes(user["enc_key"]), password)

    token = generate_token()
    expires = (_utcnow() + timedelta(minutes=30)).isoformat()
    db.create_session(user["id"], token, utcnow_iso(), expires)
    save_session(token, username, user["id"], raw_key)

    log_info("login_success", username=username)
    return token, raw_key


def logout(token: str):
    db.invalidate_session(token)
    clear_session()
    log_info("logout", token=token[:8] + "...")


def lock(token: str):
    db.invalidate_session(token)
    clear_session()
    log_info("vault_locked", token=token[:8] + "...")
