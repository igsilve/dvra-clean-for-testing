---
name: t281-follow-best-practices-when-handling-access-tokens-api-token
description: Add issuer, audience, issued-at and identifier claims, shorten the lifetime and support revocation.
---

# T281: Follow best practices when handling access tokens (API tokens)

**Category:** CODE_FIX
**SD Elements:** [T281](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T281/)
**Priority:** 8

**Finding:** Access tokens are minted with only an exp claim — no issuer, audience, jti or revocation support — and the caller chooses the lifetime.

**Code to Fix:**
```python
# app/apis/auth/utils/utils.py lines 117-125
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

**Required Fix:**
```python
# app/apis/auth/utils/utils.py
ACCESS_TOKEN_TTL = timedelta(minutes=15)


def create_access_token(data: dict) -> str:
    now = datetime.now(timezone.utc)
    to_encode = {
        **data,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
        "jti": secrets.token_urlsafe(16),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**Success Criteria:**
- Tokens carry iss, aud, iat, exp and jti, and the verifier checks all of them.
- Access token lifetime is short and refresh is a separate, revocable credential.
- A revoked jti is rejected.

**Status:** Applied
