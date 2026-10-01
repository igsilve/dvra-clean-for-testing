---
name: t1468-encrypt-sensitive-data-at-rest-in-the-browser
description: Keep the credential out of persistent client-side storage and bound its lifetime so there is nothing worth encrypting at rest in the browser.
---

# T1468: Encrypt sensitive data at rest in the browser

**Category:** CODE_FIX
**SD Elements:** [T1468](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1468/)
**Priority:** 9

**Finding:** The bearer token is handed to the client with no guidance or mechanism for protecting it at rest on the client side.

**Code to Fix:**
```python
# app/apis/auth/services/get_token_service.py lines 29-32
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
```

**Required Fix:**
```python
# app/apis/auth/services/get_token_service.py
ACCESS_TOKEN_EXPIRE_MINUTES = 15

response.set_cookie(
    "access_token",
    access_token,
    httponly=True,      # unreachable from JavaScript, never written to localStorage
    secure=True,
    samesite="strict",
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
)
```

**Success Criteria:**
- The token is never persisted in localStorage or sessionStorage.
- Credentials held by the client expire in minutes, not a week.
- Any sensitive value that must persist client side is encrypted with a key that is not also stored there.

**Status:** Applied
