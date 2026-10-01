---
name: t2349-configure-software-to-have-secure-settings-by-default
description: Remove the insecure fallbacks so the application cannot start without deliberately supplied configuration.
---

# T2349: Configure software to have secure settings by default

**Category:** CODE_FIX
**SD Elements:** [T2349](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2349/)
**Priority:** 8

**Finding:** Every security-relevant setting falls back to an insecure development default: a six-digit JWT key, the username "chef" and the database password "password".

**Code to Fix:**
```python
# app/config.py lines 26-36
class Settings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", generate_random_secret())
    CHEF_USERNAME = os.getenv("CHEF_USERNAME", "chef")

    JWT_VERIFY_SIGNATURE = os.getenv("JWT_VERIFY_SIGNATURE")

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", 5432)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "restaurant")
```

**Required Fix:**
```python
# app/config.py
def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


class Settings:
    JWT_SECRET_KEY: str = _required("JWT_SECRET_KEY")
    CHEF_USERNAME: str = _required("CHEF_USERNAME")
    POSTGRES_USER: str = _required("POSTGRES_USER")
    POSTGRES_PASSWORD: str = _required("POSTGRES_PASSWORD")
```

**Success Criteria:**
- No security-relevant setting has a hardcoded fallback value.
- Startup fails loudly when a required value is missing.
- `generate_random_secret()` is removed from the configuration module.

**Status:** Applied
