---
name: t7362-enforce-trusted-hosts-and-https-only-transport-with-starle
description: Install TrustedHostMiddleware and HTTPS enforcement so Host headers are validated and plaintext requests are redirected.
---

# T7362: Enforce trusted hosts and HTTPS-only transport with Starlette middleware (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7362](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7362/)
**Priority:** 10

**Finding:** Neither TrustedHostMiddleware nor HTTPSRedirectMiddleware is installed, so Host headers are unvalidated and plaintext HTTP is served.

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
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
if settings.ENVIRONMENT is ENV.PRODUCTION:
    app.add_middleware(HTTPSRedirectMiddleware)
```

**Success Criteria:**
- A request with `Host: attacker.example` returns 400.
- A plaintext HTTP request in production is redirected to HTTPS.
- Allowed hosts come from configuration, not a wildcard.

**Status:** Applied
