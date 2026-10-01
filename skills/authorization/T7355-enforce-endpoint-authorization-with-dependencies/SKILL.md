---
name: t7355-enforce-endpoint-authorization-with-dependencies-and-oauth
description: Attach the same role dependency to the delete route that create and update already use.
---

# T7355: Enforce endpoint authorization with dependencies and OAuth2 scopes (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7355](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7355/)
**Priority:** 10

**Finding:** Unlike create and update, the delete route depends only on get_current_user and applies no RolesBasedAuthChecker, so any authenticated customer can delete menu items.

**Code to Fix:**
```python
# app/apis/menu/services/delete_menu_item_service.py lines 12-18
@router.delete("/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    utils.delete_menu_item(db, item_id)
```

**Required Fix:**
```python
# app/apis/menu/services/delete_menu_item_service.py
@router.delete("/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE, UserRole.CHEF])),
):
    utils.delete_menu_item(db, item_id)
```

**Success Criteria:**
- Every mutating menu route requires the employee or chef role.
- A customer's DELETE /menu/{id} returns 403.
- A test covers the customer case.

**Status:** Applied
