from typing import Union

from apis.auth.utils import get_current_user, get_user_by_username
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None


@router.put("/profile", response_model=UserUpdate, status_code=status.HTTP_200_OK)
def update_profile(
    user: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    # The account being edited comes from the token, never from the body.
    # Selecting it by the submitted username let any authenticated caller
    # rewrite another person's name and phone number just by naming them.
    if user.username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized",
        )

    db_user = get_user_by_username(db, current_user.username)

    for var, value in user.dict().items():
        # username is the subject, not an editable field.
        if value and var != "username":
            setattr(db_user, var, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
