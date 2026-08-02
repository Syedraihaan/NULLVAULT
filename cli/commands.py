from database import db
from auth import manager as auth
from storage import vault
from core.session import load_session, refresh_session


def get_active_session() -> dict | None:
    session = load_session()
    if not session:
        return None
    if not db.get_session(session["token"]):
        return None
    return session


def _refresh(session: dict):
    refresh_session(session["token"], session["username"], session["user_id"], session["fernet_key"])


def cmd_register(username: str, password: str) -> str:
    return auth.register(username, password)


def cmd_login(username: str, password: str) -> str:
    auth.login(username, password)
    return "[+] Vault unlocked. Session active for 30 minutes."


def cmd_store(session: dict, path: str) -> str:
    path = path.strip().strip('"').strip("'")
    hid = vault.store(session["user_id"], path, session["fernet_key"])
    _refresh(session)
    return f"[+] Stored successfully.\n    ID : {hid}"


def cmd_get(session: dict, hash_id: str, out_dir: str = ".") -> str:
    out = vault.retrieve(session["user_id"], hash_id, out_dir, session["fernet_key"])
    _refresh(session)
    return f"[+] Restored to: {out}"


def cmd_list(session: dict) -> str:
    entries = vault.list_entries(session["user_id"])
    _refresh(session)
    if not entries:
        return "[*] Your vault is empty."
    lines = [
        "",
        f"  {'#':<4} {'TYPE':<6} {'NAME':<30} {'SIZE':>12}  {'ID':<34}  STORED AT",
        "  " + "─" * 100,
    ]
    for i, e in enumerate(entries, 1):
        size = f"{e['size_bytes']:,} B"
        tag  = "[DIR]" if e["entry_type"] == "dir" else "[FILE]"
        lines.append(
            f"  {i:<4} {tag:<6} {e['orig_name']:<30} {size:>12}  {e['hash_id']:<34}  {e['created_at']}"
        )
    lines.append("")
    return "\n".join(lines)


def cmd_delete(session: dict, hash_id: str) -> str:
    vault.delete_entry(session["user_id"], hash_id)
    _refresh(session)
    return f"[+] Entry '{hash_id[:16]}...' permanently deleted."


def cmd_logout(session: dict) -> str:
    auth.logout(session["token"])
    return "[+] Logged out. Vault sealed."


def cmd_lock(session: dict) -> str:
    auth.lock(session["token"])
    return "[+] Vault locked."
