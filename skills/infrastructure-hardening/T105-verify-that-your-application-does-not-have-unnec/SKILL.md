---
name: t105-verify-that-your-application-does-not-have-unnecessary-debu
description: Remove the diagnostic endpoint and its supporting code from the shipped application.
---

# T105: Verify that your application does not have unnecessary debug capability or leftover test/debug code

**Category:** CODE_FIX
**SD Elements:** [T105](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T105/)
**Priority:** 7

**Finding:** A debug information endpoint ships in the application and is only hidden from the OpenAPI schema.

**Code to Fix:**
```python
# app/apis/debug/services/get_debug_info_service.py lines 11-12
@router.get("/debug", status_code=status.HTTP_200_OK)
def get_debug_info_service():
```

**Required Fix:**
```python
# Delete app/apis/debug/ entirely and remove its registration:
# app/apis/router.py
- api_router.include_router(debug_router, prefix="", tags=["debug"], include_in_schema=False)

# Anything genuinely needed for operations moves behind the authenticated
# operator role and returns no environment or filesystem detail.
```

**Success Criteria:**
- The debug package no longer exists in the repository.
- No route returns process, environment or filesystem introspection.
- A test asserts GET /debug returns 404.

**Status:** Applied
