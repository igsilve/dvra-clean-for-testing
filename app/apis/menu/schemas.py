from typing import Optional

from pydantic import BaseModel, ConfigDict


class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: str
    image_url: Optional[str] = None
    description: Optional[str] = None


class MenuItem(BaseModel):
    # Validated from ORM instances, including when nested in a response
    # envelope, which does not propagate from_attributes to its members.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    category: str
    description: Optional[str] = None
    image_base64: Optional[str] = None
