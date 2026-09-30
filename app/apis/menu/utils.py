import base64

import requests
from apis.menu import schemas
from db.models import MenuItem, OrderItem
from fastapi import HTTPException


MAX_IMAGE_BYTES = 2 * 1024 * 1024
IMAGE_FETCH_TIMEOUT = (3, 5)  # (connect, read) seconds


def _image_url_to_base64(image_url: str) -> str:
    with requests.get(
        image_url, stream=True, timeout=IMAGE_FETCH_TIMEOUT, allow_redirects=False
    ) as response:
        response.raise_for_status()

        declared = response.headers.get("Content-Length")
        if declared is not None:
            try:
                if int(declared) > MAX_IMAGE_BYTES:
                    raise HTTPException(status_code=413, detail="Image too large")
            except ValueError:
                raise HTTPException(status_code=502, detail="Invalid image response")

        chunks, total = [], 0
        for chunk in response.iter_content(64 * 1024):
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=413, detail="Image too large")
            chunks.append(chunk)

    return base64.b64encode(b"".join(chunks)).decode()


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


def delete_menu_item(db, item_id: int):
    existing_order_item = (
        db.query(OrderItem).filter(OrderItem.menu_item_id == item_id).first()
    )
    if existing_order_item is not None:
        raise HTTPException(
            status_code=409,
            detail="You can not delete this menu item, it is associated with existing orders.",
        )

    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(db_item)
    db.commit()
