from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    PENDING = "Pending"
    PREPARING = "Preparing"
    ON_THE_WAY = "OnTheWay"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class OrderItem(BaseModel):
    menu_item_id: int
    quantity: int = Field(..., ge=1, le=100)


class OrderBase(BaseModel):
    delivery_address: str = Field(..., max_length=500)
    phone_number: str = Field(..., max_length=20)


class OrderCreate(OrderBase):
    items: List[OrderItem] = Field(default=[], max_length=50)
    coupon_id: Optional[int] = None


class Order(OrderBase):
    id: int
    user_id: int
    items: List[OrderItem] = []
    status: OrderStatus
    final_price: float

    class Config:
        from_attributes = True
