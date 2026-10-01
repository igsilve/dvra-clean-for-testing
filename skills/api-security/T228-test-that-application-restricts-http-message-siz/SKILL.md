---
name: t228-test-that-application-restricts-http-message-size
description: Reject oversized request bodies before they are buffered into memory.
---

# T228: Test that application restricts HTTP message size

**Category:** CODE_FIX
**SD Elements:** [T228](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T228/)
**Priority:** 9

**Finding:** The FastAPI application is constructed with no request-body size limit middleware, so an arbitrarily large body is buffered before any handler runs.

**Code to Fix:**
```python
# app/init_app.py lines 11-19
    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        servers=settings.SERVERS,
        root_path=settings.ROOT_PATH,
        docs_url=None,
        redoc_url=None,
    )
```

**Required Fix:**
```python
# app/init_app.py
MAX_BODY_BYTES = 1 * 1024 * 1024


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        declared = request.headers.get("content-length")
        if declared is not None and int(declared) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)
```

**Success Criteria:**
- A request whose Content-Length exceeds the configured ceiling is rejected with 413.
- A chunked request that streams past the ceiling is terminated rather than buffered.

**Status:** Applied
