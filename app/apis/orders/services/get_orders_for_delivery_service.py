from typing import List

from apis.auth.utils import Permission, Requires, get_current_user
from apis.orders import schemas
from db.models import Order, User
from db.session import get_db
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()

# Ceiling on the page size so a caller cannot request the whole table.
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


class DeliveryOrdersResponse(BaseModel):
    """Object envelope rather than a bare array (script-include protection)."""

    items: List[schemas.Order]


@router.get(
    "/delivery/orders",
    response_model=DeliveryOrdersResponse,
    include_in_schema=False,
)
def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    auth=Depends(Requires(Permission.READ_DELIVERY_FEED)),
):
    """
    This is a dedicated endpoint for delivery services to integrate with
    the Restaurant. Delivery services can use this endpoint to get a list of
    latest orders with their details.

    It returns every customer's delivery address and phone number, so it is
    restricted to staff. Being undocumented in the schema was never a
    control: the path is in the source, and the route answered anyone who
    asked for it.
    """
    # The bounds are declared on the parameters, so an out-of-range page size
    # is rejected with 422 before the query runs rather than quietly clamped.
    orders = (
        db.query(Order)
        .order_by(Order.date_ordered.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return DeliveryOrdersResponse(items=orders)
