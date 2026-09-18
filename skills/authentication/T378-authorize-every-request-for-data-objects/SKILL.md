---
name: t378-authorize-every-request-for-data-objects
description: Authorize every request for data objects
---

# T378: Authorize every request for data objects

**Category:** CF
**SD Elements:** [T378](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/development/4552-T378/)
**Priority:** 8

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
