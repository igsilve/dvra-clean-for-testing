---
name: t7371-emit-structured-audit-logs-without-leaking-sensitive-data
description: Configure structured logging and emit an audit record for security-relevant events without including credentials.
---

# T7371: Emit structured audit logs without leaking sensitive data (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7371](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7371/)
**Priority:** 10

**Finding:** The application factory configures no logging at all, so no structured audit record is produced for authentication, authorization or administrative actions.

**Code to Fix:**
```python
# app/init_app.py lines 10-32
def init_app():
    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        servers=settings.SERVERS,
        root_path=settings.ROOT_PATH,
        docs_url=None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*.(restaurant.com|deliveryservice.com)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(api_router)

    return app
```

**Required Fix:**
```python
# app/init_app.py
import logging
from pythonjsonlogger import jsonlogger

def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


# app/apis/auth/services/get_token_service.py
audit = logging.getLogger("audit")
audit.info("authentication", extra={
    "event": "login_succeeded",
    "username": user.username,
    "source_ip": request.client.host,
    "request_id": request.state.request_id,
})
# never log the password, the token, or the reset code
```

**Success Criteria:**
- Logging is configured once at startup with a structured formatter.
- Authentication, authorization failures, role changes and administrative actions each emit an audit record.
- No log line contains a password, token, reset code or full environment dump.
- Each record carries a correlation identifier.

**Status:** Applied
