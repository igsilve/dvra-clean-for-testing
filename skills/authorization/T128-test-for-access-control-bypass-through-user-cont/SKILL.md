---
name: t128-test-for-access-control-bypass-through-user-controlled-keys
description: Stop trusting a client-supplied username as the authorization key; resolve the subject from the authenticated principal and check the caller's privilege.
---

# T128: Test for access control bypass through user-controlled keys

**Category:** CODE_FIX
**SD Elements:** [T128](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T128/)
**Priority:** 8

**Finding:** The target account is selected by a client-supplied username and updated with no check that the caller may modify it.

**Code to Fix:**
```python
# app/apis/users/services/update_user_role_service.py lines 13-25
async def update_user_role(
    user: UserRoleUpdate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if user.role == models.UserRole.CHEF.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only Chef is authorized to add Chef role!",
        )

    db_user = update_user(db, user.username, user)
    return current_user
```

**Required Fix:**
```python
# app/apis/users/services/update_user_role_service.py
@router.put("/users/update_role", response_model=UserRead)
async def update_user_role(
    payload: UserRoleUpdate,
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    db: Session = Depends(get_db),
):
    if payload.role not in {UserRole.CUSTOMER.value, UserRole.EMPLOYEE.value}:
        raise HTTPException(status_code=400, detail="Unsupported role")

    target = get_user_by_username(db, payload.username)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = payload.role
    db.add(target); db.commit(); db.refresh(target)
    return target
```

**Success Criteria:**
- The caller's privilege is checked before any lookup driven by client input.
- A customer calling the endpoint receives 403 regardless of the username supplied.
- The response reflects the account that was actually modified.

**Status:** Applied
