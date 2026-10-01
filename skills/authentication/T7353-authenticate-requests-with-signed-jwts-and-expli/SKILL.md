---
name: t7353-authenticate-requests-with-signed-jwts-and-explicitly-pinn
description: Verify the JWT signature and pin the algorithm so a forged or unsigned token cannot authenticate.
---

# T7353: Authenticate requests with signed JWTs and explicitly pinned algorithms (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7353](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7353/)
**Priority:** 9

**Finding:** jwt.decode is called with options={"verify_signature": False}, so any unsigned or forged token is accepted.

**Code to Fix:**
```python
# app/apis/auth/utils/jwt_auth.py lines 28-33
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": VERIFY_SIGNATURE},
        )
```

**Required Fix:**
```python
# app/apis/auth/utils/jwt_auth.py
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"

payload = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=[ALGORITHM],
    options={"verify_signature": True, "verify_exp": True, "require": ["exp", "sub"]},
)
```

**Success Criteria:**
- The `VERIFY_SIGNATURE` flag is removed and verification is unconditional.
- `algorithms` is a literal list that excludes `none`.
- A token with a tampered payload returns 401.

**Status:** Applied
