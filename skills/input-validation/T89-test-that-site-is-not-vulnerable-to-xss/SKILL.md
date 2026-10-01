---
name: t89-test-that-site-is-not-vulnerable-to-xss
description: Validate stored text on input and guarantee it is never emitted into an HTML context.
---

# T89: Test that site is not vulnerable to XSS

**Category:** CODE_FIX
**SD Elements:** [T89](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T89/)
**Priority:** 8

**Finding:** Update writes caller-supplied text fields straight onto the model and back out through the API with no sanitization.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 34-55
def update_menu_item(
    db,
    item_id: int,
    menu_item: schemas.MenuItemCreate,
):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    menu_item_dict = menu_item.dict()
    image_url = menu_item_dict.pop("image_url", None)

    for key, value in menu_item_dict.items():
        setattr(db_item, key, value)

    if image_url:
        db_item.image_base64 = _image_url_to_base64(image_url)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

**Required Fix:**
```python
# app/apis/menu/utils.py
def update_menu_item(db, item_id: int, menu_item: schemas.MenuItemCreate):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # MenuItemCreate forbids extra keys and bounds every text field.
    for key, value in menu_item.model_dump(exclude_unset=True, exclude={"image_url"}).items():
        setattr(db_item, key, value)

    if menu_item.image_url:
        db_item.image_base64 = _image_url_to_base64(_safe_image_url(menu_item.image_url))

    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item
```

**Success Criteria:**
- Input models bound and constrain every text field and forbid extra keys.
- Responses are JSON with `X-Content-Type-Options: nosniff`.
- A stored `<script>` payload is returned escaped or as inert JSON data, never executed.

**Status:** Applied
