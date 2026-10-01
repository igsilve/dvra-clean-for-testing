---
name: t7369-externalize-the-jwt-signing-key-and-other-secrets-from-cod
description: Require the signing key and every other secret to come from the environment or a secret store, with no in-code fallback.
---

# T7369: Externalize the JWT signing key and other secrets from code (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7369](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7369/)
**Priority:** 10

**Finding:** JWT_SECRET_KEY falls back to an in-process generated six-digit value instead of requiring an externally supplied secret.

**Code to Fix:**
```python
# app/config.py lines 22-27
def generate_random_secret():
    return "".join(random.choices("1234567890", k=6))


class Settings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", generate_random_secret())
```

**Required Fix:**
```python
# app/config.py
def _required_secret(name: str, min_length: int = 32) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be provided by the secret store")
    if len(value) < min_length:
        raise RuntimeError(f"{name} must be at least {min_length} characters")
    return value


class Settings:
    JWT_SECRET_KEY: str = _required_secret("JWT_SECRET_KEY")
    POSTGRES_PASSWORD: str = _required_secret("POSTGRES_PASSWORD", min_length=16)

# generate_random_secret() is deleted.
```

**Success Criteria:**
- `generate_random_secret()` and every secret default are removed from the configuration module.
- Startup fails when a secret is missing or too short.
- Secrets are delivered by a secret mount, not committed configuration.
- Rotating a secret requires no code change.

**Status:** Applied
