---
name: t7356-enforce-object-level-ownership-checks-on-every-resource-ac
description: Check object ownership on every resource access, not only the caller's role.
---

# T7356: Enforce object-level ownership checks on every resource access (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7356](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7356/)
**Priority:** 8

**Finding:** No ownership predicate is applied to the queried Order before it is serialized back.

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
- Ownership is expressed as a query filter so the object is never loaded without it.
- The same pattern is applied to orders, coupons and profile access.
- Cross-account access returns 404.

**Status:** Applied
