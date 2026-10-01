---
name: t407-verify-that-symmetric-key-authentication-is-secure
description: Verify the token signature on every request and pin the accepted algorithm.
---

# T407: Verify that symmetric-key authentication is secure

**Category:** CODE_FIX
**SD Elements:** [T407](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T407/)
**Priority:** 7

**Finding:** The verifier loads the same weak symmetric key and then disables signature verification outright.

**Code to Fix:**
```python
# app/apis/auth/utils/jwt_auth.py lines 11-13
SECRET_KEY = Settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
VERIFY_SIGNATURE = False
```

**Required Fix:**
```python
# app/apis/auth/utils/jwt_auth.py
payload = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=["HS256"],
    options={"verify_signature": True, "verify_exp": True, "require": ["exp", "sub"]},
)
```

**Success Criteria:**
- No code path disables signature verification.
- The algorithm list is a fixed literal and does not include `none`.
- A token signed with a different key is rejected with 401.

**Status:** Applied
