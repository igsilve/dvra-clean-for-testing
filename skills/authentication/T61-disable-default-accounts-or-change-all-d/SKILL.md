---
name: t61-disable-default-accounts-or-change-all-d
description: Disable default accounts or change all default passwords
---

# T61: Disable default accounts or change all default passwords

**Category:** CF
**SD Elements:** [T61](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T61/)
**Priority:** 9

**Code to Fix:**
```python
# app/apis/orders/service.py line 1
from apis.orders.services.create_order_service import router as create_order_router
from apis.orders.services.get_order_service import router as get_order_router
from apis.orders.services.get_order_status import router as get_order_status_router
from apis.orders.services.get_orders_for_delivery_service import (
    router as get_orders_for_delivery_router,
)
from apis.orders.services.get_orders_service import router as get_orders_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(create_order_router)
router.include_router(get_order_router)
```

**Required Fix:**
```python
# Apply least privilege, input validation, secure defaults, and explicit authorization checks.
# Implement the control described by the countermeasure in this code path.
```

**Success Criteria:**
- Countermeasure requirements are implemented and verifiable in code and tests.

**Status:** Applied
