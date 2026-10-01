---
name: t2600-control-the-result-set-size-returned-by-a-query
description: Cap the number of rows any listing endpoint will return regardless of the requested limit.
---

# T2600: Control the result set size returned by a query

**Category:** CODE_FIX
**SD Elements:** [T2600](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2600/)
**Priority:** 7

**Finding:** `limit` is an unconstrained integer query parameter passed straight into .limit(), so a caller can request an unbounded result set.

**Code to Fix:**
```python
# app/apis/orders/services/get_orders_for_delivery_service.py lines 17-32
def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    This is a dedicated endpoint for delivery services to integrate with
    the Restaurant. Delivery services can use this endpoint to get a list of
    latest orders with their details.
    """
    orders = (
        db.query(Order)
        .order_by(Order.date_ordered.desc())
        .offset(skip)
        .limit(limit)
        .all()
```

**Required Fix:**
```python
# app/apis/orders/services/get_orders_for_delivery_service.py
from fastapi import Query

MAX_PAGE_SIZE = 100


def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    ...
):
    orders = db.query(Order).order_by(Order.date_ordered.desc()).offset(skip).limit(limit).all()
```

**Success Criteria:**
- Every paginated endpoint declares `le=` on its limit parameter.
- A request for limit=100000 is rejected with 422 rather than served.

**Status:** Applied
