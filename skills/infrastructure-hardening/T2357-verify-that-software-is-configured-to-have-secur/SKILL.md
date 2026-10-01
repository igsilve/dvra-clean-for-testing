---
name: t2357-verify-that-software-is-configured-to-have-secure-settings
description: Add a startup assertion and a test that prove the secure defaults hold.
---

# T2357: Verify that software is configured to have secure settings by default

**Category:** CODE_FIX
**SD Elements:** [T2357](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2357/)
**Priority:** 8

**Finding:** The insecure fallbacks apply silently whenever the environment variables are absent, so there is no secure-by-default baseline to verify.

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
# app/tests/security/test_secure_defaults.py
@pytest.mark.security
@pytest.mark.parametrize("name", ["JWT_SECRET_KEY", "POSTGRES_PASSWORD", "CHEF_USERNAME"])
def test_startup_fails_without_required_setting(monkeypatch, name):
    monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError):
        importlib.reload(config)
```

**Success Criteria:**
- A test asserts the application refuses to start for each missing required setting.
- A test asserts no default value equals a known weak literal.

**Status:** Applied
