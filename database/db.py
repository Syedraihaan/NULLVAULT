import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / ".nullvault_storage" / "vault.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                password_hash TEXT  NOT NULL,
                enc_key     BLOB    NOT NULL,
                is_decoy    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                token       TEXT    NOT NULL UNIQUE,
                created_at  TEXT    NOT NULL,
                expires_at  TEXT    NOT NULL,
                is_active   INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS files (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                hash_id     TEXT    NOT NULL UNIQUE,
                orig_name   TEXT    NOT NULL,
                size_bytes  INTEGER NOT NULL,
                sha256      TEXT    NOT NULL,
                entry_type  TEXT    NOT NULL DEFAULT 'file',
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS login_attempts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL,
                success     INTEGER NOT NULL,
                attempted_at TEXT   NOT NULL
            );
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Users ──────────────────────────────────────────────────────────────────

def create_user(username: str, password_hash: str, enc_key: bytes, created_at: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, enc_key, created_at) VALUES (?,?,?,?)",
            (username, password_hash, enc_key, created_at),
        )


def get_user(username: str) -> sqlite3.Row | None:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def create_decoy_user(username: str, password_hash: str, enc_key: bytes, created_at: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, enc_key, is_decoy, created_at) VALUES (?,?,?,1,?)",
            (username, password_hash, enc_key, created_at),
        )


# ── Sessions ───────────────────────────────────────────────────────────────

def create_session(user_id: int, token: str, created_at: str, expires_at: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, token, created_at, expires_at) VALUES (?,?,?,?)",
            (user_id, token, created_at, expires_at),
        )


def get_session(token: str) -> sqlite3.Row | None:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM sessions WHERE token = ? AND is_active = 1", (token,)
        ).fetchone()


def invalidate_session(token: str):
    with _conn() as conn:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE token = ?", (token,))


def invalidate_all_sessions(user_id: int):
    with _conn() as conn:
        conn.execute("UPDATE sessions SET is_active = 0 WHERE user_id = ?", (user_id,))


# ── Files ──────────────────────────────────────────────────────────────────

def insert_file(user_id: int, hash_id: str, orig_name: str, size_bytes: int, sha256: str, created_at: str, entry_type: str = "file"):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO files (user_id, hash_id, orig_name, size_bytes, sha256, entry_type, created_at) VALUES (?,?,?,?,?,?,?)",
            (user_id, hash_id, orig_name, size_bytes, sha256, entry_type, created_at),
        )


def get_file(user_id: int, hash_id: str) -> sqlite3.Row | None:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM files WHERE user_id = ? AND hash_id = ?", (user_id, hash_id)
        ).fetchone()


def list_files(user_id: int) -> list:
    with _conn() as conn:
        return conn.execute(
            "SELECT hash_id, orig_name, size_bytes, sha256, entry_type, created_at FROM files WHERE user_id = ?",
            (user_id,),
        ).fetchall()


def delete_file_record(user_id: int, hash_id: str):
    with _conn() as conn:
        conn.execute(
            "DELETE FROM files WHERE user_id = ? AND hash_id = ?", (user_id, hash_id)
        )


# ── Login attempts ─────────────────────────────────────────────────────────

def record_attempt(username: str, success: bool, attempted_at: str):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO login_attempts (username, success, attempted_at) VALUES (?,?,?)",
            (username, int(success), attempted_at),
        )


def recent_failed_attempts(username: str, since: str) -> int:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE username=? AND success=0 AND attempted_at >= ?",
            (username, since),
        ).fetchone()
        return row[0]
