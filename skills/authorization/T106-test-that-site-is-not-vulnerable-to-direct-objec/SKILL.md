---
name: t106-test-that-site-is-not-vulnerable-to-direct-object-access-at
description: Scope the order lookup to the calling user so an identifier from the URL cannot reach another customer's record.
---

# T106: Test that site is not vulnerable to direct object access attacks

**Category:** CODE_FIX
**SD Elements:** [T106](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T106/)
**Priority:** 8

**Finding:** The order is fetched by path id and returned without comparing Order.user_id to the caller.

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
@router.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.CUSTOMER])),
):
    db_order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
```

**Success Criteria:**
- The ownership predicate is part of the query, not a post-hoc check.
- Requesting another customer's order id returns 404, not 403.
- A test covers the cross-account case.

**Status:** Applied
