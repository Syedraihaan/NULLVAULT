import os
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

PBKDF2_ITERATIONS = 480_000
SALT_SIZE = 32


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from a password using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def generate_user_key() -> bytes:
    """Generate a fresh Fernet key for a user."""
    return Fernet.generate_key()


def encrypt_user_key(raw_key: bytes, password: str) -> bytes:
    """Encrypt the user's Fernet key with a password-derived key.
    Returns: salt (32) + ciphertext
    """
    salt = secrets.token_bytes(SALT_SIZE)
    wrapping_key = derive_key(password, salt)
    return salt + Fernet(wrapping_key).encrypt(raw_key)


def decrypt_user_key(blob: bytes, password: str) -> bytes:
    """Decrypt the user's Fernet key blob."""
    salt, ciphertext = blob[:SALT_SIZE], blob[SALT_SIZE:]
    wrapping_key = derive_key(password, salt)
    return Fernet(wrapping_key).decrypt(ciphertext)


def encrypt_data(data: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(data)


def decrypt_data(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


def rotate_key(old_key: bytes, new_key: bytes, ciphertext: bytes) -> bytes:
    """Re-encrypt data from old_key to new_key."""
    plaintext = decrypt_data(ciphertext, old_key)
    return encrypt_data(plaintext, new_key)
