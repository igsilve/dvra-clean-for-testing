---
name: t378-authorize-every-request-for-data-objects
description: Authorize each data object individually, not just the caller's role.
---

# T378: Authorize every request for data objects

**Category:** CODE_FIX
**SD Elements:** [T378](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T378/)
**Priority:** 8

**Finding:** A role check is present but no per-object authorization is performed on the requested order.

**Code to Fix:**
```python
# app/apis/orders/services/get_order_service.py lines 11-20
@router.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.CUSTOMER])),
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
```

**Required Fix:**
```python
# app/apis/orders/services/get_order_service.py
db_order = (
    db.query(Order)
    .filter(Order.id == order_id, Order.user_id == current_user.id)
    .first()
)
if db_order is None:
    raise HTTPException(status_code=404, detail="Order not found")
```

**Success Criteria:**
- Every route that accepts a resource identifier constrains the query by the owning principal.
- Employee and chef access to another user's record goes through an explicit, audited permission.

**Status:** Applied
