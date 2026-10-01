---
name: t7354-hash-user-passwords-with-argon2-or-bcrypt-via-a-vetted-lib
description: Pin a modern password hash with explicit cost parameters rather than relying on library defaults.
---

# T7354: Hash user passwords with Argon2 or bcrypt via a vetted library (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7354](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7354/)
**Priority:** 10

**Finding:** The password context pins bcrypt with deprecated="auto" and no explicit cost factor, and Argon2 is not offered.

**Code to Fix:**
```python
# app/apis/auth/utils/utils.py lines 13-21
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)
```

**Required Fix:**
```python
# app/apis/auth/utils/utils.py
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Success Criteria:**
- Argon2id is the preferred scheme with bcrypt retained only for verification of existing hashes.
- Cost parameters are set explicitly and reviewed.
- Legacy hashes are upgraded transparently on successful login.

**Status:** Applied
