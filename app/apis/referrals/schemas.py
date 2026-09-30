from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DiscountCouponRead(BaseModel):
    # Validated from ORM instances nested in DiscountCouponsResponse.
    model_config = ConfigDict(from_attributes=True)

    id: int
    discount_percentage: int
    used: bool
    created_at: datetime
    used_at: Optional[datetime]
