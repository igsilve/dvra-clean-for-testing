---
name: t7363-add-security-response-headers-via-middleware-fastapi
description: Add a middleware that sets the standard security response headers on every reply.
---

# T7363: Add security response headers via middleware (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7363](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7363/)
**Priority:** 8

**Finding:** The middleware stack adds CORS and a rate-limit handler but no security response headers.

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
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers.pop("X-Powered-By", None)
        return response


app.add_middleware(SecurityHeadersMiddleware)
```

**Success Criteria:**
- nosniff, frame options, referrer policy, CSP and HSTS are present on every response.
- No response advertises the framework or language version.

**Status:** Applied
