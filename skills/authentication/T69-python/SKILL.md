---
name: strong-passwords-server-to-server-system-accounts
description: Strong password requirements for server-to-server system accounts; use when system/service accounts have weaker or separate password rules than end users
---

# Strong password requirements for server-to-server system accounts

## What This Skill Does
Ensures server-to-server (system/service) accounts use at least the same strong password policy as end users by centralizing password validation, reusing it everywhere system credentials are created/updated, and enforcing it for configuration/secret-based passwords used in server-to-server authentication.

## Decision Table
| Situation | Action |
|-----------|--------|
| System/service account passwords are validated with simpler/shorter rules than end users | Create a shared password policy function and make system-account validation delegate to it |
| Separate functions exist for user and system password validation | Refactor both to call a single central `validatePasswordPolicy` (or equivalent) and remove weaker system-specific baselines |
| System account password is loaded from config/env/secret store without validation | Run it through the shared password validator during bootstrap and fail fast if it does not comply |
| System account creation/rotation code paths do not call any password validator | Insert a call to the shared validator before persisting or activating new passwords and reject on failure |
| Code already uses one shared validator for all account types and validates configuration passwords on startup | No action needed; keep policy centralized and update only in that single place |

## Boundaries

### Can Do
- Unify password rules so system accounts and end users share the same minimum strength policy.
- Identify and refactor scattered password checks into a single reusable password-validation function.
- Enforce strong password checks on configuration/secret-based system account credentials used for server-to-server authentication.

### Cannot Do
- Select or configure production-grade password hashing/KDF algorithms (PBKDF2, bcrypt, Argon2) beyond simple examples.
- Replace broader authentication mechanisms (OAuth, MTLS, API keys, tokens); this skill only addresses password strength parity.
- Fix unrelated issues such as hardcoded credentials, rotation frequency, or excessive privileges, except where they intersect with password policy use.

## Gotchas
- Assuming config/secret-store passwords are “trusted”: They still must pass the shared policy, or weak credentials silently reach production.
- Creating a new “system-only” validator that relaxes rules: This reintroduces the weakness; system-specific checks may only add stricter rules, never weaken the shared baseline.
- Updating user password rules but not reusing the same function for system accounts: If you edit only user-facing validators, system accounts will lag behind and remain weaker over time.

## Quick Verification
```bash
# 1. Run vulnerable version and confirm weak system password works
python app_vulnerable_code.py password

# 2. Run vulnerable version with a wrong password and see failure
python app_vulnerable_code.py WrongPass123!

# 3. Run fixed version: weak password from env/config should be rejected
S2S_ACCOUNT_PASSWORD=password python app_fix_gpt51_code.py  # expect error on startup

# 4. Run fixed version with strong, policy-compliant password
S2S_ACCOUNT_PASSWORD='Str0ng!Passw0rd123' python app_fix_gpt51_code.py  # expect normal run

# 5. Spot-check shared policy parity in REPL (Python example)
python - << 'EOF'
from app_fix_gpt51_code import validate_user_password, validate_system_account_password
for pw in ["short", "password", "WeakPass1", "Str0ng!Passw0rd123"]:
    print(pw, validate_user_password(pw), validate_system_account_password(pw))
EOF
```