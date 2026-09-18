from typing import Union

from apis.auth.utils import get_current_user, get_user_by_username
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from pydantic import constr
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


class UserUpdate(BaseModel):
    first_name: Union[
        constr(strip_whitespace=True, min_length=1, max_length=64, regex=r"^[A-Za-z0-9 .,'-]+$"),
        None,
    ] = None
    last_name: Union[
        constr(strip_whitespace=True, min_length=1, max_length=64, regex=r"^[A-Za-z0-9 .,'-]+$"),
        None,
    ] = None
    phone_number: Union[str, None] = None


@router.put("/profile", response_model=UserUpdate, status_code=status.HTTP_200_OK)
def update_profile(
    user: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    db_user = get_user_by_username(db, current_user.username)

    for var, value in user.dict().items():
        if value:
            setattr(db_user, var, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
