---
name: t167-test-that-the-application-is-not-vulnerable-to-json-hijacki
description: Wrap collection responses in a JSON object so the reply is never a bare top-level array that a foreign page can read.
---

# T167: Test that the application is not vulnerable to JSON Hijacking

**Category:** CODE_FIX
**SD Elements:** [T167](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T167/)
**Priority:** 7

**Finding:** The endpoint returns a top-level JSON array of order records to a GET request, which is the classic shape exploited by JSON hijacking when the response is reachable with ambient credentials.

**Code to Fix:**
```python
# app/apis/orders/services/get_orders_service.py lines 14-29
@router.get("/orders", response_model=List[schemas.Order])
def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.CUSTOMER])),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return orders
```

**Required Fix:**
```python
# app/apis/orders/services/get_orders_service.py
class OrderListResponse(BaseModel):
    items: List[schemas.Order]


@router.get("/orders", response_model=OrderListResponse)
def get_orders(...):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .offset(skip)
        .limit(min(limit, 100))
        .all()
    )
    return OrderListResponse(items=orders)
```

**Success Criteria:**
- No endpoint returns a top-level JSON array.
- Collection endpoints respond with an object whose payload sits under a named key.
- Responses are served with `Content-Type: application/json` and are not executable as script.

**Status:** Applied
