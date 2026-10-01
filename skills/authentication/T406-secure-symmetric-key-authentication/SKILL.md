---
name: t406-secure-symmetric-key-authentication
description: Load the symmetric signing key from a secret store with a minimum length, and fail startup if it is absent.
---

# T406: Secure symmetric-key authentication

**Category:** CODE_FIX
**SD Elements:** [T406](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T406/)
**Priority:** 7

**Finding:** The symmetric HS256 signing key is taken from Settings.JWT_SECRET_KEY, which falls back to a six-digit random value.

**Code to Fix:**
```python
# app/apis/auth/utils/utils.py lines 10-11
SECRET_KEY = Settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
```

**Required Fix:**
```python
# app/config.py
class Settings:
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]   # no fallback

    def __init__(self):
        if len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters")
```

**Success Criteria:**
- The process refuses to start without an externally supplied key.
- Keys shorter than 32 bytes are rejected.
- No key material is generated inside the application.

**Status:** Applied
