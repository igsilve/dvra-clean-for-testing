---
name: t1363-verify-if-message-throttling-is-properly-performed-in-web
description: Apply the configured slowapi limiter to the routes it was introduced for so request throttling is actually enforced.
---

# T1363: Verify if message throttling is properly performed in Web APIs

**Category:** CODE_FIX
**SD Elements:** [T1363](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1363/)
**Priority:** 8

**Finding:** A slowapi Limiter is constructed with no default limits, and no route in the application applies @limiter.limit, so no API throttling is actually enforced.

**Code to Fix:**
```python
# app/rate_limiting.py lines 1-4
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

**Required Fix:**
```python
# app/rate_limiting.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

# app/apis/auth/services/get_token_service.py
@router.post("/token")
@limiter.limit("5/minute")
async def get_token(request: Request, ...):
    ...
```

**Success Criteria:**
- The Limiter is constructed with a default limit.
- Authentication, password-reset and admin routes carry an explicit, tighter @limiter.limit decorator.
- Exceeding a limit returns HTTP 429 with a Retry-After header.

**Status:** Applied
