---
name: t536-restrict-the-size-of-incoming-messages-in-services
description: Enforce a maximum accepted message size for every service endpoint.
---

# T536: Restrict the size of incoming messages in services

**Category:** CODE_FIX
**SD Elements:** [T536](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T536/)
**Priority:** 8

**Finding:** No maximum request size is enforced at the application or middleware layer.

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
MAX_BODY_BYTES = 1 * 1024 * 1024        # general JSON payloads
MAX_UPLOAD_BYTES = 5 * 1024 * 1024      # routes that accept binary content

app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)
```

**Success Criteria:**
- A global body-size ceiling is applied by middleware, not per handler.
- Routes needing a larger ceiling opt in explicitly rather than the default being generous.

**Status:** Applied
