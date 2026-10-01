---
name: t119-test-for-clickjacking
description: Emit framing-protection headers on every response so the application cannot be embedded in an attacker-controlled page.
---

# T119: Test for clickjacking

**Category:** CODE_FIX
**SD Elements:** [T119](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T119/)
**Priority:** 7

**Finding:** No middleware sets X-Frame-Options or a Content-Security-Policy frame-ancestors directive, so any page can frame the application's responses.

**Code to Fix:**
```python
# app/init_app.py lines 20-29
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*.(restaurant.com|deliveryservice.com)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Required Fix:**
```python
# app/init_app.py
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        return response


app.add_middleware(SecurityHeadersMiddleware)
```

**Success Criteria:**
- Every response carries `X-Frame-Options: DENY` and a CSP containing `frame-ancestors 'none'`.
- A page that embeds the application in an iframe fails to render it.

**Status:** Applied
