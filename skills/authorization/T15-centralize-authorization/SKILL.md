---
name: t15-centralize-authorization
description: Route every authorization decision through one shared policy layer instead of re-implementing checks in individual handlers.
---

# T15: Centralize authorization

**Category:** CODE_FIX
**SD Elements:** [T15](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T15/)
**Priority:** 9

**Finding:** RolesBasedAuthChecker is the only shared authorization primitive and it covers roles alone; ownership and resource rules are re-implemented ad hoc in individual handlers.

**Code to Fix:**
```python
# app/apis/auth/utils/roles_based_auth_checker.py lines 6-17
class RolesBasedAuthChecker:
    def __init__(
        self,
        required_roles,
    ):
        self.required_roles = required_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.required_roles:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return True
```

**Required Fix:**
```python
# app/apis/auth/utils/authz.py
class Permission(str, enum.Enum):
    READ_DISK_STATS = "read:disk_stats"
    MANAGE_MENU = "manage:menu"
    MANAGE_ROLES = "manage:roles"


ROLE_PERMISSIONS = {
    UserRole.CHEF: {Permission.READ_DISK_STATS, Permission.MANAGE_MENU, Permission.MANAGE_ROLES},
    UserRole.EMPLOYEE: {Permission.MANAGE_MENU},
    UserRole.CUSTOMER: set(),
}


class Requires:
    def __init__(self, permission: Permission):
        self.permission = permission

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if self.permission not in ROLE_PERMISSIONS.get(user.role, set()):
            raise HTTPException(status_code=403, detail="Unauthorized")
        return user
```

**Success Criteria:**
- All routes declare their requirement through the shared dependency.
- No handler body contains an inline role comparison.
- Adding a role or permission requires a change in exactly one module.

**Status:** Applied
