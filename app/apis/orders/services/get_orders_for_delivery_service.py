from typing import List

from apis.auth.utils import RolesBasedAuthChecker, get_current_user
from apis.orders import schemas
from db.models import Order, User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.get(
    "/delivery/orders",
    response_model=List[schemas.Order],
    include_in_schema=False,
)
def get_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    auth=Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE])),
    db: Session = Depends(get_db),
):
    """
    This is a dedicated endpoint for delivery services to integrate with
    the Restaurant. Delivery services can use this endpoint to get a list of
    latest orders with their details.
    """
    orders = (
        db.query(Order)
        .order_by(Order.date_ordered.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return orders
