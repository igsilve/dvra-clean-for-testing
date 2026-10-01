---
name: t66-prevent-web-pages-from-being-loaded-inside-iframe
description: Deny framing of the application through response headers set for every route.
---

# T66: Prevent web pages from being loaded inside iFrame

**Category:** CODE_FIX
**SD Elements:** [T66](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T66/)
**Priority:** 7

**Finding:** No framing protection header is emitted by the middleware stack.

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
response.headers["X-Frame-Options"] = "DENY"
response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; default-src 'self'"
```

**Success Criteria:**
- Framing directives are present on every response including error responses.
- No route opts out of the header middleware.

**Status:** Applied
