---
name: t7368-protect-cookie-authenticated-routes-with-samesite-cookies
description: If the token is placed in a cookie, set SameSite, Secure and HttpOnly and pair it with a CSRF token; otherwise keep it out of cookies entirely.
---

# T7368: Protect cookie-authenticated routes with SameSite cookies and CSRF tokens (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7368](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7368/)
**Priority:** 7

**Finding:** The access token is returned in the response body with no cookie attributes and no CSRF token issued alongside it.

**Code to Fix:**
```python
# app/apis/auth/services/get_token_service.py lines 26-32
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
```

**Required Fix:**
```python
# app/apis/auth/services/get_token_service.py
response.set_cookie(
    "access_token",
    access_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=int(access_token_expires.total_seconds()),
    path="/",
)
response.set_cookie("csrf_token", secrets.token_urlsafe(32), secure=True, samesite="strict")
# every state-changing route then compares the X-CSRF-Token header to the cookie
```

**Success Criteria:**
- No authentication cookie is set without HttpOnly, Secure and SameSite.
- Every state-changing route rejects a request whose CSRF header does not match the cookie.
- A cross-site form POST against a state-changing route fails.

**Status:** Applied
