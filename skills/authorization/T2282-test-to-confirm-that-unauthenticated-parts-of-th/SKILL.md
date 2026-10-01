---
name: t2282-test-to-confirm-that-unauthenticated-parts-of-the-applicat
description: Close the routes that are reachable without authentication and confirm the remaining public surface is intentional.
---

# T2282: Test to confirm that unauthenticated parts of the application are accessible

**Category:** CODE_FIX
**SD Elements:** [T2282](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2282/)
**Priority:** 8

**Finding:** The /debug route is registered with no authentication dependency and is reachable anonymously.

**Code to Fix:**
```python
# app/apis/debug/services/get_debug_info_service.py lines 11-12
@router.get("/debug", status_code=status.HTTP_200_OK)
def get_debug_info_service():
```

**Required Fix:**
```python
# app/apis/router.py
PUBLIC_ROUTES = {"/healthcheck", "/token", "/register"}

# The debug router is removed entirely:
# api_router.include_router(debug_router, ...)   <- delete

# Everything else is mounted behind an authenticated dependency:
api_router.include_router(
    orders_router, prefix="", tags=["orders"],
    dependencies=[Depends(get_current_user)],
)
```

**Success Criteria:**
- The set of anonymous routes is declared explicitly and reviewed.
- An automated test walks app.routes and fails on any unlisted route without an auth dependency.
- /debug is no longer registered.

**Status:** Applied
