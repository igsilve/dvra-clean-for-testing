---
name: t7365-rate-limit-authentication-and-expensive-endpoints-fastapi
description: Rate-limit the authentication and password-reset endpoints, which are the cheapest targets for credential guessing.
---

# T7365: Rate-limit authentication and expensive endpoints (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7365](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7365/)
**Priority:** 10

**Finding:** The token endpoint carries no rate-limit decorator, so password guessing is unthrottled.

**Code to Fix:**
```python
# app/apis/auth/services/get_token_service.py lines 16-21
@router.post("/token")
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
```

**Required Fix:**
```python
# app/apis/auth/services/get_token_service.py
from rate_limiting import limiter


@router.post("/token")
@limiter.limit("5/minute")
async def get_token(request: Request, form_data: ..., db: Session = Depends(get_db)) -> Token:
    ...
```

**Success Criteria:**
- /token, /register, /reset-password and /reset-password/new-password each carry an explicit limit.
- The sixth login attempt within a minute from one source returns 429.
- Limits are keyed on both source address and submitted username.

**Status:** Applied
