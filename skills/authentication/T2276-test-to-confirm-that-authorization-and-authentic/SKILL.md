---
name: t2276-test-to-confirm-that-authorization-and-authentication-cont
description: Require authentication and authorization on every route, including ones hidden from the OpenAPI schema.
---

# T2276: Test to confirm that authorization and authentication controls are in place for access to resources

**Category:** CODE_FIX
**SD Elements:** [T2276](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2276/)
**Priority:** 7

**Finding:** The delivery orders endpoint declares no authentication or authorization dependency and is merely hidden from the schema.

**Code to Fix:**
```python
# app/apis/orders/services/get_orders_for_delivery_service.py lines 12-21
@router.get(
    "/delivery/orders",
    response_model=List[schemas.Order],
    include_in_schema=False,
)
def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
```

**Required Fix:**
```python
# app/apis/orders/services/get_orders_for_delivery_service.py
@router.get("/delivery/orders", response_model=OrderListResponse, include_in_schema=False)
def get_orders(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE, UserRole.CHEF]))],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ...
```

**Success Criteria:**
- Enumerating the route table shows no handler without an authentication dependency, except the documented public ones.
- `include_in_schema=False` is never the only thing protecting a route.
- An anonymous request to /delivery/orders and /debug returns 401 or 404.

**Status:** Applied
