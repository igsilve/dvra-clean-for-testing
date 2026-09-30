from apis.auth.utils import AuthzContext, Permission, Requires, get_current_user
from apis.menu import schemas, utils
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.put(
    "/menu", response_model=schemas.MenuItem, status_code=status.HTTP_201_CREATED
)
def create_menu_item(
    menu_item: schemas.MenuItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(Requires(Permission.MANAGE_MENU)),
):
    db_item = utils.create_menu_item(db, menu_item, AuthzContext(actor=current_user))
    return db_item
