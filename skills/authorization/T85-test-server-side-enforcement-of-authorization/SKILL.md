---
name: t85-test-server-side-enforcement-of-authorization
description: Enforce the role requirement server side on the role-update route instead of relying on a single negative check.
---

# T85: Test server-side enforcement of authorization

**Category:** CODE_FIX
**SD Elements:** [T85](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T85/)
**Priority:** 8

**Finding:** The only server-side check rejects the Chef role; every other role change is applied to any username without verifying the caller's privileges.

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
    ...
```

**Success Criteria:**
- The route rejects any caller who is not a chef, before inspecting the body.
- The set of assignable roles is an explicit allow-list.
- A customer calling the route receives 403.

**Status:** Applied
