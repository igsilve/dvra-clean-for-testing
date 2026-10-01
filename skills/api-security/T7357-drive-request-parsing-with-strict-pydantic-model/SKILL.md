---
name: t7357-drive-request-parsing-with-strict-pydantic-models-and-forb
description: Forbid unknown fields in request models so client input cannot introduce attributes that later get written onto ORM objects.
---

# T7357: Drive request parsing with strict Pydantic models and forbid extra fields (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7357](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7357/)
**Priority:** 10

**Finding:** The profile update model is declared with extra=Extra.allow, so unknown client-supplied fields survive validation and are later assigned onto the ORM object.

**Code to Fix:**
```python
# app/apis/auth/services/patch_profile_service.py lines 22-25
class UserUpdate(BaseModel, extra=Extra.allow):
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None
```

**Required Fix:**
```python
# app/apis/auth/services/patch_profile_service.py
from pydantic import BaseModel, ConfigDict


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None


@router.patch("/profile", response_model=UserRead, status_code=status.HTTP_200_OK)
def patch_profile(user: UserUpdate, ...):
    db_user = get_user_by_username(db, current_user.username)
    for field, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)
```

**Success Criteria:**
- No request model in the codebase is declared with `extra=Extra.allow` or `extra="allow"`.
- A PATCH body containing `{"role": "Chef"}` returns 422 instead of being applied.
- Attribute assignment iterates the declared model fields, never arbitrary client keys.

**Status:** Applied
