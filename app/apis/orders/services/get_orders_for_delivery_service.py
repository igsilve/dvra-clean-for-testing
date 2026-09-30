from typing import List

from apis.orders import schemas
from db.models import Order
from db.session import get_db
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    """
    This is a dedicated endpoint for delivery services to integrate with
    the Restaurant. Delivery services can use this endpoint to get a list of
    latest orders with their details.
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
