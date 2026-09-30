from apis.auth.utils import get_current_user, owned_by
from apis.orders.utils import fetch_order_status_from_delivery_service
from db.models import Order, OrderStatus, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


class OrderStatusResponse(BaseModel):
    status: str
    order_id: int


def _owned_order(order_id: int, current_user: User, db: Session) -> Order:
    """Load an order the caller is entitled to see.

    Ownership is a filter on the query rather than a comparison after
    loading, so the row is never in memory unauthorised. The rule itself
    lives in the authorization module: staff who read the delivery feed are
    exempt, and this handler does not need to know that.
    """
    db_order = (
        owned_by(db.query(Order), Order, current_user)
        .filter(Order.id == order_id)
        .first()
    )
    # A 404 rather than a 403 for someone else's order: a distinct response
    # would confirm the order exists.
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return db_order


@router.get("/orders/status/{order_id}", response_model=OrderStatusResponse)
def get_order_status(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Return the stored status of an order.

    Read-only: refreshing from the delivery service writes to the database and
    therefore lives on the POST route below.
    """
    db_order = _owned_order(order_id, current_user, db)

    return OrderStatusResponse(
        order_id=db_order.id,
        status=db_order.status.value
        if isinstance(db_order.status, OrderStatus)
        else str(db_order.status),
    )


@router.post(
    "/orders/status/{order_id}/refresh",
    response_model=OrderStatusResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_order_status(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Sync an order's status from the delivery service and persist it."""
    db_order = _owned_order(order_id, current_user, db)

    delivery_data = fetch_order_status_from_delivery_service(order_id)

    # The status comes from an external service, so it is untrusted input:
    # accept it only if it names a known OrderStatus, and assign through the
    # ORM so the value is bound rather than interpolated into SQL.
    try:
        new_status = OrderStatus[delivery_data["status"]]
    except KeyError:
        raise HTTPException(
            status_code=502, detail="Delivery service returned an unknown status"
        )

    db_order.status = new_status
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return OrderStatusResponse(order_id=db_order.id, status=db_order.status.value)
