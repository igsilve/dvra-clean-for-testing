---
name: t15-centralize-authorization
description: Centralize authorization
---

# T15: Centralize authorization

**Category:** CF
**SD Elements:** [T15](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/architecture-design/4552-T15/)
**Priority:** 9

**Code to Fix:**
```python
# app/apis/auth/service.py line 1
from apis.auth.services.get_profile_service import router as get_profile_router
from apis.auth.services.get_token_service import router as get_token_router
from apis.auth.services.patch_profile_service import router as patch_profile_router
from apis.auth.services.register_user_service import router as register_user_router
from apis.auth.services.reset_password_new_password_service import (
    router as reset_password_new_password_router,
)
from apis.auth.services.reset_password_service import router as reset_password_router
from apis.auth.services.update_profile_service import router as update_profile_router
from fastapi import APIRouter

router = APIRouter()
```

**Required Fix:**
```python
# Apply least privilege, input validation, secure defaults, and explicit authorization checks.
# Implement the control described by the countermeasure in this code path.
```

**Success Criteria:**
- Countermeasure requirements are implemented and verifiable in code and tests.

**Status:** Applied
