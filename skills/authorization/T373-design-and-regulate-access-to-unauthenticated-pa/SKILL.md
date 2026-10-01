---
name: t373-design-and-regulate-access-to-unauthenticated-parts-of-the
description: Declare the unauthenticated surface deliberately and mount every other router behind an authentication dependency.
---

# T373: Design and regulate access to unauthenticated parts of the application

**Category:** CODE_FIX
**SD Elements:** [T373](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T373/)
**Priority:** 8

**Finding:** Routers are mounted without an explicit policy separating the authenticated surface from the anonymous one; /debug and /delivery/orders end up public by omission.

**Code to Fix:**
```python
# app/apis/router.py lines 12-22
api_router = APIRouter()
api_router.include_router(healthcheck_router, prefix="", tags=["healthcheck"])
api_router.include_router(
    debug_router, prefix="", tags=["debug"], include_in_schema=False
)
api_router.include_router(menu_router, prefix="", tags=["menu"])
api_router.include_router(orders_router, prefix="", tags=["orders"])
api_router.include_router(auth_router, prefix="", tags=["auth"])
api_router.include_router(admin_router, prefix="", tags=["admin"])
api_router.include_router(users_router, prefix="", tags=["users"])
api_router.include_router(referrals_router, prefix="", tags=["referrals"])
```

**Required Fix:**
```python
# app/apis/router.py
api_router = APIRouter()

# Public routes:
api_router.include_router(healthcheck_router, prefix="", tags=["healthcheck"])
api_router.include_router(auth_router, prefix="", tags=["auth"])

# Authenticated:
authed = [Depends(get_current_user)]
api_router.include_router(menu_router, prefix="", tags=["menu"], dependencies=authed)
api_router.include_router(orders_router, prefix="", tags=["orders"], dependencies=authed)
api_router.include_router(admin_router, prefix="", tags=["admin"], dependencies=authed)
api_router.include_router(users_router, prefix="", tags=["users"], dependencies=authed)
api_router.include_router(referrals_router, prefix="", tags=["referrals"], dependencies=authed)
```

**Success Criteria:**
- Routers are mounted in two explicit groups: anonymous and authenticated.
- Adding a router without choosing a group fails review, and the default is authenticated.
- The anonymous group exposes no data belonging to a user.

**Status:** Applied
