import sys
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from database.db import init_db, get_user
from auth.manager import register, login
from storage.vault import store, list_entries, retrieve, delete_entry

init_db()

# Register
try:
    register("vaulttest", "T3stP@ss99!")
    print("[1] Registered OK")
except ValueError:
    print("[1] User exists, continuing")

# Login
token, key = login("vaulttest", "T3stP@ss99!")
uid = get_user("vaulttest")["id"]
print(f"[2] Login OK  uid={uid}")

# --- Test 1: store a single FILE ---
file_src = r"C:\Users\syedh\OneDrive\Desktop\MYSELF\offer letter\OfferLetter_Sheik_Nifla_NULLGRIDSLabs.docx"
hid_file = store(uid, file_src, key)
print(f"[3] File stored  hash_id={hid_file[:16]}...")

# --- Test 2: store a DIRECTORY ---
dir_src = r"C:\Users\syedh\OneDrive\Desktop\MYSELF\offer letter"
hid_dir = store(uid, dir_src, key)
print(f"[4] Directory stored  hash_id={hid_dir[:16]}...")

# List
entries = list_entries(uid)
print(f"[5] Vault has {len(entries)} entries:")
for e in entries:
    print(f"     [{e['entry_type'].upper()}] {e['orig_name']}  |  {e['hash_id'][:16]}...")

# Retrieve file
out_file = retrieve(uid, hid_file, r"C:\Users\syedh\OneDrive\Desktop\nullvault_test_out", key)
print(f"[6] File retrieved to: {out_file}")

# Retrieve directory
out_dir = retrieve(uid, hid_dir, r"C:\Users\syedh\OneDrive\Desktop\nullvault_test_out", key)
print(f"[7] Directory retrieved to: {out_dir}")

# Delete both
delete_entry(uid, hid_file)
delete_entry(uid, hid_dir)
print(f"[8] Both deleted. Remaining: {len(list_entries(uid))}")

print("\nALL TESTS PASSED")
