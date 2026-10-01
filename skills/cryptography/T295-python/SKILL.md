---
name: avoid-storing-unencrypted-confidential-data-without-access-control-mechanisms
description: Use when Python code writes sensitive data to files or local databases in plaintext, or stores encryption material in source/config instead of protected secret storage.
---
# Avoid storing unencrypted confidential data without access control mechanisms

## What This Skill Does
This skill fixes cleartext storage of sensitive information in Python applications by ensuring confidential data is encrypted before any file or local database write, and by moving encryption keys, certificates, and passwords out of source code or plaintext configuration into a secure secret retrieval path. Prefer authenticated encryption such as `cryptography.fernet.Fernet`, keep encryption/decryption in storage or data-access wrappers, and fail closed if secret lookup is missing or invalid.

## Decision Table
| Situation | Action |
|-----------|--------|
| Sensitive values are written with `open(..., "w")`, `Path.write_text()`, `json.dump()`, or similar plaintext file APIs | Wrap the persistence path so data is serialized, encrypted with `Fernet(...).encrypt(...)`, and only ciphertext bytes are written with binary file APIs |
| Sensitive fields are inserted or updated in `sqlite3` or another local database as plaintext strings | Encrypt the sensitive field before `execute()`/`executemany()` so the database stores ciphertext, not plaintext |
| Encryption keys, passwords, or certificates are read from hard-coded literals, repo files, or plaintext config | Replace with a centralized secret retrieval function using secure storage such as `keyring.get_password()` or a fail-closed environment-backed secret interface |
| Code already encrypts sensitive data before persistence and decrypts only on authorized read paths | No action needed |
| Stored ciphertext must detect tampering | Use authenticated encryption like `cryptography.fernet.Fernet`; do not replace it with reversible encoding such as Base64 |

## Boundaries

### Can Do
- Add a centralized encryption/decryption wrapper for sensitive file storage
- Encrypt sensitive database fields before insert or update operations
- Replace hard-coded or plaintext secret loading with a secure secret-access abstraction

### Cannot Do
- Decide which business fields are sensitive without code or domain clues
- Provide or manage external secret infrastructure beyond the application integration point
- Guarantee OS-level file permissions, disk encryption, or database access control by itself

## Gotchas
- Writing JSON and then Base64-encoding it: Base64 is encoding, not encryption, so the secret remains recoverable
- Encrypting only on reads or after writing temp/cache/export files: plaintext may already have reached disk before protection is applied
- Keeping a fallback hard-coded key when secret lookup fails: this defeats secret storage and prevents fail-closed behavior

## Quick Verification
```bash
# Confirm authenticated encryption or secure secret retrieval exists
rg -n 'Fernet\s*\(|\.encrypt\s*\(|keyring\.get_password\s*\(' .

# Find likely unguarded plaintext file writes or local DB writes that may bypass the fix
rg -n 'json\.dump\s*\(|open\s*\([^)]*,\s*["'\'']w["'\'']|Path\([^)]*\)\.write_text\s*\(|write_text\s*\(|sqlite3\..*execute\s*\(|\.execute\s*\(' .

# Build/test check for Python projects of different shapes
python -m compileall .
python -m pytest -q
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T295 in this project because of its survey answers. Copied verbatim from SD Elements.

### Serialized objects

Do not store serialized objects with fields that contain confidential data, in an unencrypted format. Data in serialized objects is easy to extract and read without additional protection such as encryption.
