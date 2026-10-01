---
name: use-approved-cryptographic-algorithms
description: Use approved cryptographic algorithms, key sizes, IV handling, and password hashing in Python; Use when code uses weak crypto, fixed IVs, encoding as encryption, or general-purpose hashes for passwords
---

# Use correct and approved cryptographic algorithms, parameters, and key lengths

## What This Skill Does
This skill replaces weak or misleading cryptographic patterns in Python with approved primitives and safer usage rules. Apply it when code uses obsolete algorithms, fixed or reused CBC IVs, Base64 or compression as if it provided confidentiality, insecure key generation or reuse, or general-purpose hashes for password storage. The fix uses real encryption such as `AESGCM` or correctly implemented AES-CBC with a fresh random 16-byte IV, enforces valid AES key lengths, separates encoding from encryption, generates keys with `secrets`, tracks key purpose and status, and uses dedicated password hashing such as `hashlib.pbkdf2_hmac()` with a unique random salt.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code uses `base64.b64encode()`, compression, or similar reversible transforms to "protect" sensitive data | Replace with real encryption such as `cryptography.hazmat.primitives.ciphers.aead.AESGCM`; keep Base64 only as transport encoding after encryption |
| Code uses weak or obsolete crypto, or AES with invalid key lengths | Replace with approved AES key sizes only (`16`, `24`, `32` bytes) and prefer authenticated encryption like `AESGCM` |
| Code uses `modes.CBC(...)` with a constant, derived, reused, or non-random IV | Generate a fresh IV with `secrets.token_bytes(16)` for every encryption and store/transmit it with the ciphertext |
| Code hashes passwords with `hashlib.md5()`, `hashlib.sha1()`, `hashlib.sha256()`, or plain `hashlib.new()` | Replace with `hashlib.pbkdf2_hmac("sha256", ...)` using a unique random salt per password record |
| Code already uses approved algorithms, valid key sizes, fresh IVs/nonces, purpose-bound active keys, and dedicated password hashing | No action needed |

## Boundaries

### Can Do
- Replace encoding-as-encryption patterns with real encryption and keep encoding separate
- Enforce approved AES key sizes and fresh random IV generation for AES-CBC
- Replace insecure password hashing with salted `hashlib.pbkdf2_hmac()` and verification using `secrets.compare_digest()`

### Cannot Do
- Design or validate a full enterprise key management system or HSM integration
- Guarantee cryptographic policy compliance beyond the code visible in the repository
- Infer business-specific key lifetimes, rotation schedules, or recovery procedures without requirements

## Gotchas
- Using Base64 after encryption is fine, but using Base64 instead of encryption is wrong: encoding is reversible and provides no confidentiality
- Using AES-CBC without a fresh random 16-byte IV is wrong: constant or reused IVs leak structure across messages
- Using `hashlib.sha256(password)` for password storage is wrong: general-purpose hashing is too fast and lacks the dedicated salt-and-work-factor behavior needed for passwords

## Quick Verification
```bash
# Confirm approved crypto wrappers/usages exist
rg -n 'AESGCM|pbkdf2_hmac|secrets\.token_bytes\(16\)|secrets\.token_bytes\(32\)|compare_digest|modes\.CBC\(' .

# Find unguarded dangerous patterns that should be replaced or reviewed
rg -n 'base64\.b64encode\(|base64\.b64decode\(|hashlib\.(md5|sha1|sha224|sha256|sha512)\(|modes\.CBC\((b["'\''].*|iv\s*=\s*b["'\''].*|[A-Za-z_][A-Za-z0-9_]*\))' .

# Build + test with generic Python toolchain commands
python -m compileall .
python -m unittest discover -v
```