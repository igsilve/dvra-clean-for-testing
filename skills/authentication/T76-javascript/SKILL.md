---
name: do-not-hardcode-passwords
description: Use when JavaScript code embeds passwords, API keys, tokens, or secret fallbacks in source and must be changed to load and validate secrets from runtime configuration.
---
# Do not hardcode passwords

## What This Skill Does
This skill removes hardcoded passwords and other secrets from JavaScript source code and replaces them with centralized runtime secret loading, validation, and safe use. Apply it when code compares user input to embedded secret literals, stores reusable credentials in source, uses insecure fallback defaults like `process.env.SECRET || 'secret'`, or logs secret-bearing values. It also covers password hashing for stored user credentials and encrypted local config handling when file-based secret storage is unavoidable.

## Decision Table
| Situation | Action |
|-----------|--------|
| A password, token, API key, or DB credential appears as a string literal in JavaScript code | Replace the literal with a runtime loader such as `requireEnv()` or `getConfiguredAdminPassword()` and fail closed when missing |
| Code uses `process.env.SECRET || 'default-secret'` or similar fallback literals | Remove the fallback literal and require a non-empty runtime value |
| Code compares a runtime input directly to a loaded secret with `===` | Replace with a constant-time comparison using `crypto.timingSafeEqual` via a helper like `timingSafeEqualString()` |
| Code stores or verifies user passwords | Store password hashes with `bcryptjs` and verify with `bcrypt.compareSync()` or equivalent |
| Secrets are already loaded from runtime config, validated, redacted from logs, and no source literals remain | No action needed |

## Boundaries

### Can Do
- Replace hardcoded secret literals with runtime configuration reads such as `process.env`
- Centralize secret loading and validate missing, empty, malformed, or placeholder values before use
- Convert plaintext password storage or checks to password-hash verification with `bcryptjs`

### Cannot Do
- Provision a real secret manager, environment variables, or deployment-time secret injection outside the codebase
- Recover safe secret values or generate production credentials for the application
- Guarantee that comments, tests, fixtures, committed `.env` files, build artifacts, or logs contain no secrets without broader review

## Gotchas
- Replacing a hardcoded secret with `process.env.SECRET || 'changeme'`: this is still a hardcoded fallback and defeats the fix
- Using `===` for secret comparison after moving the secret to config: the secret is no longer hardcoded, but direct comparison can still leak timing information
- Logging `process.env`, request bodies, or decrypted config objects: this can re-expose secrets even after source literals are removed

## Quick Verification
```bash
# Confirm secure runtime secret loading / guard helpers exist
rg -n "process\.env\.[A-Z0-9_]+|requireEnv\(|requireRuntimeSecret\(|getConfiguredAdminPassword\(|timingSafeEqualString\(|bcrypt\.(hashSync|compareSync)\(" .

# Find likely unguarded hardcoded secrets or insecure secret fallbacks
rg -n "(PASSWORD|PASS|SECRET|TOKEN|API_KEY|ACCESS_KEY|PRIVATE_KEY)[A-Z0-9_ \t]*=[ \t]*['\"][^'\"]+['\"]|process\.env\.[A-Z0-9_]+[ \t]*\|\|[ \t]*['\"][^'\"]+['\"]|===\s*(ADMIN_PASSWORD|.*SECRET|.*TOKEN)|\b(ADMIN_PASSWORD|DB_PASSWORD|API_KEY|SECRET)\b" .

# Build + test with the available JavaScript toolchain
npm test || yarn test || pnpm test
```