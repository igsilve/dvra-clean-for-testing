from typing import List

from apis.auth.utils import get_current_user
from apis.orders import schemas
from db.models import Order, User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.get(
    "/delivery/orders",
    response_model=List[schemas.Order],
    include_in_schema=False,
)
def get_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    This is a dedicated endpoint for delivery services to integrate with
    the Restaurant. Delivery services can use this endpoint to get a list of
    latest orders with their details.
    """
    if current_user.role not in (UserRole.CHEF.value, UserRole.EMPLOYEE.value):
        raise HTTPException(status_code=403, detail="Unauthorized")

    safe_limit = min(max(limit, 1), 100)
    orders = (
        db.query(Order)
        .order_by(Order.date_ordered.desc())
        .offset(skip)
        .limit(safe_limit)
        .all()
    )
    return orders
