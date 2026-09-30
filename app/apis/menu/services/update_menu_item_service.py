from apis.auth.utils import AuthzContext, Permission, Requires, get_current_user
from apis.menu import schemas, utils
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.put("/menu/{item_id}", response_model=schemas.MenuItem)
def update_menu_item(
    item_id: int,
    menu_item: schemas.MenuItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(Requires(Permission.MANAGE_MENU)),
):
    db_item = utils.update_menu_item(
        db, item_id, menu_item, AuthzContext(actor=current_user)
    )
    return db_item
