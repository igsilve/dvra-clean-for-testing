---
name: t7366-validate-and-safely-store-uploaded-files-fastapi
description: Validate the type, magic bytes and size of any binary content before storing it.
---

# T7366: Validate and safely store uploaded files (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7366](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7366/)
**Priority:** 10

**Finding:** Remote image bytes are base64-encoded and stored with no content-type check, no magic-byte validation and no size limit.

**Code to Fix:**
```python
# app/apis/menu/utils.py lines 16-31
def create_menu_item(
    db,
    menu_item: schemas.MenuItemCreate,
):
    menu_item_dict = menu_item.dict()
    image_url = menu_item_dict.pop("image_url", None)
    db_item = MenuItem(**menu_item_dict)

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
from PIL import Image

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _store_image(content: bytes) -> str:
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in ALLOWED_FORMATS:
                raise HTTPException(status_code=400, detail="Unsupported image format")
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Not a valid image")

    return base64.b64encode(content).decode()
```

**Success Criteria:**
- Content type is determined from the bytes, not from a client-supplied header or extension.
- Only an explicit allow-list of formats is accepted.
- A size ceiling is enforced before decoding.
- Stored content is never served with a content type derived from user input.

**Status:** Applied
