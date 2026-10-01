---
name: secure-one-time-passwords
description: Use when Python code generates, stores, or verifies OTPs with predictable randomness, plaintext values, replay risk, long lifetimes, or missing attempt limits.
---
# Secure one-time passwords (OTP)

## What This Skill Does
This skill hardens Python OTP flows against predictable generation, replay, brute-force guessing, plaintext storage, and timing leaks. Apply it when code issues or verifies one-time passwords for login, MFA, recovery, or step-up authentication. The fix replaces non-cryptographic randomness with `secrets` or standard `pyotp` HOTP/TOTP flows, enforces short expiration and single-use semantics, stores only an HMAC-derived value when storage is required, uses `hmac.compare_digest()` for verification, and adds retry limits so repeated guesses are rejected.

## Decision Table
| Situation | Action |
|-----------|--------|
| OTP generation uses `random.randint`, `random.randrange`, `random.choice`, or seeded `random` | Apply this fix: replace with `secrets.randbelow()` / `secrets.choice()` for custom OTPs |
| App-based OTP flow is custom-built and can use a standard algorithm | Replace with `pyotp.TOTP` or `pyotp.HOTP`; store only the shared secret |
| OTP is stored as plaintext like `otp`, `code`, or `record["otp"]` | Store only an HMAC-derived value with a server-side key, then verify with `hmac.compare_digest()` |
| Verification allows long validity, repeated success, or unlimited failures | Add `expires_at`, single-use consumption (`used_at` or deletion), and per-account / per-source attempt limits |
| Code already uses `secrets` or `pyotp`, short expiry, single-use, constant-time compare, and attempt limits | No action needed |

## Boundaries

### Can Do
- Replace insecure Python OTP generation with `secrets` or `pyotp`
- Add expiration, single-use consumption, and bounded verification windows
- Change plaintext OTP persistence to keyed-hash storage and constant-time comparison

### Cannot Do
- Guarantee SMS, email, or push delivery channel security
- Choose product-specific retry thresholds or user experience policies without project guidance
- Safely rotate existing OTP secrets or migrate persistence schemas without checking application compatibility

## Gotchas
- Using `hashlib.sha256(otp)` without a server-side key: this is weaker than HMAC and makes stored OTPs easier to attack if the store is exposed
- Marking OTPs as used after returning success but not atomically with verification: concurrent requests can reuse the same OTP
- Switching to TOTP but allowing a large `valid_window`: this quietly accepts stale codes and weakens the short-lived nature of OTPs

## Quick Verification
```bash
# Confirm secure OTP patterns exist
rg -n "secrets\.(randbelow|choice)|pyotp\.(TOTP|HOTP|random_base32)|hmac\.compare_digest|expires_at|used_at|max_attempts|attempts" .

# Find unguarded dangerous OTP generation/storage/compare patterns
rg -n "random\.(randint|randrange|choice)|random\.seed|record\[['\"]otp['\"]\]|\.otp\b|==\s*provided_otp|==\s*stored_otp|24\s*\*\s*60\s*\*\s*60" .

# Build + test with the Python toolchain
python -m compileall .
python -m pytest -q
```