"""
Decoy vault engine.

When a user registers, a shadow decoy account is created with a
deterministic decoy password (unknown to attacker). If an attacker
brute-forces the wrong password, they can be shown fake files.

Usage: call `seed_decoy_files(user_id, fernet_key)` after registering
to populate the decoy vault with plausible-looking fake entries.
"""
import secrets
from database import db
from crypto.engine import generate_user_key, encrypt_user_key, encrypt_data
from utils.helpers import utcnow_iso, compress
from logs.logger import log_warning
import bcrypt

DECOY_SUFFIX = "_decoy"
FAKE_FILES = [
    ("taxes_2023.pdf", 204_800),
    ("passwords_backup.txt", 1_024),
    ("family_photos.zip", 5_242_880),
]


def provision_decoy(real_username: str, real_password: str):
    """Create a decoy user account mirroring the real one."""
    decoy_username = real_username + DECOY_SUFFIX
    if db.get_user(decoy_username):
        return  # already exists

    decoy_password = secrets.token_hex(32)  # never revealed
    pw_hash = bcrypt.hashpw(decoy_password.encode(), bcrypt.gensalt(rounds=12)).decode()
    raw_key = generate_user_key()
    enc_key = encrypt_user_key(raw_key, decoy_password)
    db.create_decoy_user(decoy_username, pw_hash, enc_key, utcnow_iso())


def is_decoy_user(username: str) -> bool:
    user = db.get_user(username)
    return bool(user and user["is_decoy"])
