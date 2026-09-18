---
name: do-not-hardcode-passwords
description: Use when code embeds passwords, API tokens, or secret keys in source and they must be moved to runtime inputs or encrypted external configuration.
---

# Do not hardcode passwords

## What This Skill Does
This skill removes hardcoded passwords, secret keys, and API tokens from application source and replaces them with runtime-loaded secrets from environment variables or external configuration. When secrets must be stored outside memory, it enforces encrypted-only configuration entries with required metadata, runtime key derivation, authenticated decryption, and fail-fast rejection of plaintext secret properties.

## Decision Table
| Situation | Action |
|-----------|--------|
| Passwords, tokens, or secret keys appear as string literals, constants, or inline constructor arguments in source code | Apply this fix: move secret loading to runtime input or external configuration and remove the hardcoded literal |
| A config file contains plaintext secret properties such as `db.password=secret123` | Replace plaintext entries with encrypted-only secret fields and reject plaintext properties at startup |
| Secrets are persisted outside memory for later use | Store only encrypted values plus required metadata (`.enc`, `.iv`, `.salt`, `.iterations`, `.keyLength`) and decrypt at runtime |
| Java code derives keys or decrypts stored secrets | Use PBKDF2WithHmacSHA256 with per-secret random salt and AES/GCM/NoPadding with a unique random IV |
| Code already loads secrets from runtime inputs or encrypted external config and rejects plaintext fallback | No action needed |

## Boundaries

### Can Do
- Replace hardcoded secret literals with environment-variable or external-config loading
- Enforce encrypted-only configuration structure for stored secrets
- Add fail-fast validation for missing, blank, malformed, or plaintext secret properties

### Cannot Do
- Provision a real secret manager, rotate existing credentials, or clean leaked secrets from repository history
- Guarantee all sensitive values are fully erased from memory in every library or runtime
- Invent deployment-specific secret sources beyond the app's available runtime inputs and configuration model

## Gotchas
- Leaving a plaintext fallback property in config: this defeats the fix because the app may still accept an exposed secret
- Using plain `String` everywhere for secret handling: immutable strings can linger in memory longer than needed
- Encrypting stored secrets without authentication: unauthenticated encryption can allow tampered ciphertext to be accepted

## Quick Verification
```bash
# Find likely hardcoded secrets in Java source
grep -RInE 'password|secret|token|api[_-]?key|private static final String .*=' src/

# Confirm plaintext secret properties are rejected
printf 'admin.password=secret123\n' > /tmp/app-secrets.properties
APP_SECRET_CONFIG=/tmp/app-secrets.properties APP_MASTER_PASSWORD=test ./gradlew test

# Confirm startup or login fails when required runtime inputs are missing
env -u APP_MASTER_PASSWORD -u APP_SECRET_CONFIG ./gradlew test
```