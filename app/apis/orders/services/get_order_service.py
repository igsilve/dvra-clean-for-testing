from apis.auth.utils import Permission, Requires, get_current_user, owned_by
from apis.orders import schemas
from db.models import Order, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(Requires(Permission.READ_OWN_ORDERS)),
):
    # Ownership is part of the query, so another customer's row is never
    # loaded. A 404 rather than a 403: a distinct response would confirm
    # the order exists and let an attacker enumerate ids.
    db_order = (
        owned_by(db.query(Order), Order, current_user)
        .filter(Order.id == order_id)
        .first()
    )
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
