---
name: t7411-implement-controls-for-content-intended-to-be-displayed-as
description: Constrain stored text fields and mark them as text so consumers render them safely.
---

# T7411: Implement controls for content intended to be displayed as text

**Category:** CODE_FIX
**SD Elements:** [T7411](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7411/)
**Priority:** 7

**Finding:** Menu item name and description are accepted as free text and persisted with no output-encoding contract.

**Code to Fix:**
```python
# app/apis/menu/services/create_menu_item_service.py lines 15-22
def create_menu_item(
    menu_item: schemas.MenuItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE, UserRole.CHEF])),
):
    db_item = utils.create_menu_item(db, menu_item)
    return db_item
```

**Required Fix:**
```python
# app/apis/menu/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class MenuItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=60)
    image_url: str | None = None
```

**Success Criteria:**
- Text fields declare length limits and reject unknown keys.
- Responses are served as application/json with nosniff, so text is never interpreted as markup.
- No stored text is concatenated into HTML anywhere in the service.

**Status:** Applied
