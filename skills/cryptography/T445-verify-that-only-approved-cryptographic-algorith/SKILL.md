---
name: t445-verify-that-only-approved-cryptographic-algorithms-and-key
description: Use an approved algorithm with a key of adequate length, supplied externally.
---

# T445: Verify that only approved cryptographic algorithms and key lengths are used

**Category:** CODE_FIX
**SD Elements:** [T445](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T445/)
**Priority:** 8

**Finding:** HS256 is used with a key that defaults to six decimal digits, far below any approved key-length requirement.

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
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]   # >= 32 bytes, from the secret store
    JWT_ALGORITHM: str = "HS256"                         # or RS256 with a managed key pair

    def __init__(self):
        if len(self.JWT_SECRET_KEY.encode()) < 32:
            raise RuntimeError("JWT_SECRET_KEY must provide at least 256 bits")
```

**Success Criteria:**
- The signing key is at least 256 bits.
- The algorithm is an approved one and is pinned at both signing and verification.
- Startup fails when the key is too short or missing.

**Status:** Applied
