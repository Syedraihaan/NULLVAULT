# NullVault

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Encryption](https://img.shields.io/badge/Encryption-AES--Fernet-critical)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-informational)

> **Everything stored here is void. Nothing exists without the key.**

A secure, encrypted local storage engine for files and folders. NullVault encrypts everything at rest using a per-user Fernet key — your data is completely unreadable without your credentials.

---

## Features

- AES-based encryption via the `cryptography` library (Fernet)
- bcrypt password hashing with 12 rounds
- PBKDF2-HMAC-SHA256 key derivation (480,000 iterations)
- Session management with automatic expiry and vault locking
- Store and retrieve individual files or entire folders
- Brute-force lockout after 5 failed attempts (15-minute cooldown)
- Decoy vault support — fake entries shown to unauthorized access attempts

---

## Requirements

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

On first run, register a new vault with a username and password (min. 8 characters). After login, you can:

| Option | Action |
|--------|--------|
| 1 | Store a file or folder |
| 2 | Retrieve an entry |
| 3 | List vault contents |
| 4 | Delete an entry |
| 5 | Lock vault |
| 6 | Logout |

---

## How It Works

NullVault uses a two-layer encryption model:

```
Password
   │
   ▼
PBKDF2-HMAC-SHA256 (480,000 iterations + 32-byte random salt)
   │
   ▼
Wrapping Key  ──►  Encrypts  ──►  User Fernet Key (stored in DB)
                                         │
                                         ▼
                               Encrypts all vault files
```

1. **Registration** — A unique Fernet key is generated for your vault. That key is encrypted using a wrapping key derived from your password via PBKDF2-HMAC-SHA256 with a random 32-byte salt. Only the encrypted blob is stored — never the raw key.

2. **Login** — Your password re-derives the wrapping key, decrypts the Fernet key blob, and loads it into memory for the session. Sessions expire after 30 minutes of inactivity.

3. **File storage** — Files and folders are read, compressed, encrypted with your Fernet key, and written to `.nullvault_storage/`. The original filenames and contents are never stored in plaintext.

4. **Decoy vault** — On registration, a shadow decoy account is silently created with a secret random password. If an attacker gains access, they can be shown plausible-looking fake files instead of your real data.

---

## Security Notes

- **Lost password = lost data.** There is no password recovery. Your Fernet key is only recoverable with your original password — if you forget it, your vault contents are permanently inaccessible.
- **Lost database = lost data.** The `.nullvault_storage/vault.db` file contains your encrypted key blob. Without it, encrypted files cannot be decrypted even with the correct password.
- **Session keys are in-memory only.** Your decrypted Fernet key is never written to disk. Locking or logging out immediately clears it from memory.
- **Brute-force protection.** After 5 failed login attempts, the account is locked for 15 minutes.
- **No plaintext leakage.** Entry names, file contents, and folder structures are all encrypted before storage.

---

## Project Structure

```
nullvault/
├── auth/        # Authentication & session management
├── cli/         # CLI command handlers
├── core/        # Session logic & decoy vault
├── crypto/      # Encryption engine (PBKDF2 + Fernet)
├── database/    # SQLite database layer
├── logs/        # Logging
├── storage/     # Vault file storage
├── utils/       # Helpers
└── main.py      # Entry point
```

## Storage

Encrypted files are stored locally under `.nullvault_storage/`. The vault database is never readable without the correct credentials.

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change. Keep PRs focused and minimal.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push and open a Pull Request

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT) — free to use, modify, and distribute with attribution.
