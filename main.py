import os
import sys
import getpass
from database import db
from cli.commands import (
    get_active_session,
    cmd_register, cmd_login,
    cmd_store, cmd_get, cmd_list,
    cmd_delete, cmd_logout, cmd_lock,
)

# ── ANSI colours ───────────────────────────────────────────────────────────
R  = "\033[91m"   # red
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
C  = "\033[96m"   # cyan
W  = "\033[97m"   # white
DIM = "\033[2m"
RST = "\033[0m"

# ── ASCII logo ─────────────────────────────────────────────────────────────
LOGO = f"""{R}
  ███╗   ██╗██╗   ██╗██╗     ██╗    ██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗
  ████╗  ██║██║   ██║██║     ██║    ██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝
  ██╔██╗ ██║██║   ██║██║     ██║    ██║   ██║███████║██║   ██║██║     ██║
  ██║╚██╗██║██║   ██║██║     ██║    ╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║
  ██║ ╚████║╚██████╔╝███████╗███████╗╚████╔╝ ██║  ██║╚██████╔╝███████╗██║
  ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝ ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝
{DIM}  ░░  Secure Encrypted Local Storage Engine  ·  void-class protection  ░░{RST}
"""

TAGLINE = f"{DIM}  Everything stored here is void. Nothing exists without the key.{RST}"

# ── Helpers ────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header(subtitle: str = ""):
    clear()
    print(LOGO)
    if subtitle:
        print(f"  {C}{subtitle}{RST}\n")
    print(f"  {'─' * 70}\n")


def prompt(label: str) -> str:
    return input(f"  {Y}›{RST} {label}: ").strip()


def secret(label: str) -> str:
    return getpass.getpass(f"  {Y}›{RST} {label}: ")


def info(msg: str):
    print(f"\n  {G}{msg}{RST}")


def warn(msg: str):
    print(f"\n  {R}{msg}{RST}")


def pause():
    input(f"\n  {DIM}Press Enter to continue...{RST}")


# ── Menus ──────────────────────────────────────────────────────────────────

def menu_guest():
    """Main menu when no session is active."""
    while True:
        header("Access Portal")
        print(f"  {W}  1{RST}  →  Register new vault")
        print(f"  {W}  2{RST}  →  Login to vault")
        print(f"  {W}  0{RST}  →  Exit\n")
        choice = prompt("Select")

        if choice == "1":
            do_register()
        elif choice == "2":
            session = do_login()
            if session:
                menu_vault(session)
        elif choice == "0":
            clear()
            print(f"\n  {DIM}Vault sealed. Goodbye.{RST}\n")
            sys.exit(0)
        else:
            warn("Invalid option.")
            pause()


def menu_vault(session: dict):
    """Main menu when authenticated."""
    while True:
        # Re-validate session on every loop iteration
        session = get_active_session()
        if not session:
            warn("Session expired. Please login again.")
            pause()
            return  # drop back to guest menu

        header(f"Vault  ·  {C}{session['username']}{RST}")
        print(f"  {W}  1{RST}  →  Store file or folder")
        print(f"  {W}  2{RST}  →  Retrieve entry")
        print(f"  {W}  3{RST}  →  List vault contents")
        print(f"  {W}  4{RST}  →  Delete entry")
        print(f"  {W}  5{RST}  →  Lock vault")
        print(f"  {W}  6{RST}  →  Logout\n")
        choice = prompt("Select")

        if choice == "1":
            do_store(session)
        elif choice == "2":
            do_get(session)
        elif choice == "3":
            do_list(session)
        elif choice == "4":
            do_delete(session)
        elif choice == "5":
            result = cmd_lock(session)
            info(result)
            pause()
            return
        elif choice == "6":
            result = cmd_logout(session)
            info(result)
            pause()
            return
        else:
            warn("Invalid option.")
            pause()


# ── Actions ────────────────────────────────────────────────────────────────

def do_register():
    header("Register")
    username = prompt("Username")
    if not username:
        warn("Username cannot be empty.")
        pause()
        return
    password = secret("Password")
    confirm  = secret("Confirm password")
    if password != confirm:
        warn("Passwords do not match.")
        pause()
        return
    if len(password) < 8:
        warn("Password must be at least 8 characters.")
        pause()
        return
    try:
        result = cmd_register(username, password)
        info(result)
    except ValueError as e:
        warn(str(e))
    pause()


def do_login() -> dict | None:
    header("Login")
    username = prompt("Username")
    password = secret("Password")
    try:
        cmd_login(username, password)
        session = get_active_session()
        if session:
            info(f"Welcome back, {session['username']}. Vault unlocked.")
            pause()
            return session
    except PermissionError as e:
        warn(str(e))
        pause()
    return None


def do_store(session: dict):
    header("Store File or Folder")
    print(f"  {DIM}Tip: Works with both files and folders.{RST}")
    print(f"  {DIM}      e.g.  C:\\Users\\you\\docs\\report.pdf{RST}")
    print(f"  {DIM}      or    C:\\Users\\you\\projects\\my_folder{RST}\n")
    path = prompt("Full path")
    path = path.strip().strip('"').strip("'")
    if not path:
        warn("No path entered.")
        pause()
        return
    try:
        result = cmd_store(session, path)
        info(result)
    except FileNotFoundError as e:
        warn(f"Path not found: {e}")
    except Exception as e:
        warn(f"Error: {e}")
    pause()


def do_get(session: dict):
    header("Retrieve Entry")
    listing = cmd_list(session)
    print(listing)
    entry_id = prompt("Entry ID to retrieve")
    if not entry_id:
        warn("No ID entered.")
        pause()
        return
    out_dir = prompt("Output directory (leave blank for current dir)")
    if not out_dir:
        out_dir = "."
    try:
        result = cmd_get(session, entry_id, out_dir)
        info(result)
    except (FileNotFoundError, ValueError) as e:
        warn(str(e))
    pause()


def do_list(session: dict):
    header("Vault Contents")
    result = cmd_list(session)
    print(result)
    pause()


def do_delete(session: dict):
    header("Delete Entry")
    listing = cmd_list(session)
    print(listing)
    entry_id = prompt("Entry ID to delete")
    if not entry_id:
        warn("No ID entered.")
        pause()
        return
    confirm = prompt(f"Type 'DELETE' to confirm permanent deletion")
    if confirm != "DELETE":
        warn("Deletion cancelled.")
        pause()
        return
    try:
        result = cmd_delete(session, entry_id)
        info(result)
    except FileNotFoundError as e:
        warn(str(e))
    pause()


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    db.init_db()

    # If a valid session already exists, go straight to vault menu
    session = get_active_session()
    if session:
        header(f"Resuming session for {session['username']}")
        info(f"Session still active. Welcome back, {session['username']}.")
        pause()
        menu_vault(session)
    else:
        menu_guest()


if __name__ == "__main__":
    main()
