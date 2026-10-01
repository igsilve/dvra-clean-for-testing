---
name: t96-test-if-your-site-is-vulnerable-to-csrf
description: Require a CSRF token, or an equivalent non-ambient credential, on every state-changing request.
---

# T96: Test if your site is vulnerable to CSRF

**Category:** CODE_FIX
**SD Elements:** [T96](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T96/)
**Priority:** 7

**Finding:** A state-changing PATCH is accepted with no CSRF token and no origin check.

**Code to Fix:**
```python
# app/apis/auth/services/patch_profile_service.py lines 28-33
@router.patch("/profile", response_model=UserRead, status_code=status.HTTP_200_OK)
def patch_profile(
    user: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
```

**Required Fix:**
```python
# app/init_app.py
class CsrfMiddleware(BaseHTTPMiddleware):
    SAFE = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request, call_next):
        if request.method not in self.SAFE and "access_token" in request.cookies:
            header = request.headers.get("X-CSRF-Token")
            cookie = request.cookies.get("csrf_token")
            if not header or not cookie or not secrets.compare_digest(header, cookie):
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)
        return await call_next(request)
```

**Success Criteria:**
- Every non-idempotent route rejects a request without a valid CSRF token when cookie authentication is in play.
- The comparison uses a constant-time function.
- A cross-origin form POST to /profile fails.

**Status:** Applied
