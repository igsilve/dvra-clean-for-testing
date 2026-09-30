from typing import List

from apis.auth.utils import RolesBasedAuthChecker, get_current_user
from apis.orders import schemas
from db.models import Order, User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()

# Ceiling on the page size so a caller cannot request the whole table.
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


class OrdersResponse(BaseModel):
    """Object envelope rather than a bare array (script-include protection)."""

    items: List[schemas.Order]


@router.get("/orders", response_model=OrdersResponse)
def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.CUSTOMER])),
):
    # The bounds are declared on the parameters, so an out-of-range page size
    # is rejected with 422 before the query runs rather than quietly clamped.
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return OrdersResponse(items=orders)
