from apis.auth.utils import get_current_user
from apis.menu import utils
from db.models import User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.delete("/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.CHEF.value:
        raise HTTPException(status_code=403, detail="Only Chef can delete menu items")

    utils.delete_menu_item(db, item_id)
