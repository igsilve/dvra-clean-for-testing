---
name: t86-test-session-id-uniqueness-and-rotation-after-authentication
description: Give each issued token a unique identifier and invalidate any prior session on authentication.
---

# T86: Test session ID uniqueness and rotation after authentication

**Category:** CODE_FIX
**SD Elements:** [T86](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T86/)
**Priority:** 9

**Finding:** A new access token is minted with no session identifier, no jti and no invalidation of tokens issued before authentication.

**Code to Fix:**
```python
# app/apis/auth/services/get_token_service.py lines 28-32
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
```

**Required Fix:**
```python
# app/apis/auth/utils/utils.py
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "exp": now + (expires_delta or timedelta(minutes=15)),
        "iat": now,
        "jti": secrets.token_urlsafe(16),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**Success Criteria:**
- Every token carries a unique jti, plus iat, iss and aud claims.
- Two tokens issued for the same user are never identical.
- Authentication invalidates any session identifier held before the login.

**Status:** Applied
