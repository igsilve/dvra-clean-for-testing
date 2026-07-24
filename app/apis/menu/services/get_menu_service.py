from typing import List

from apis.menu import schemas
from db.models import MenuItem
from db.session import get_db
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/menu", response_model=List[schemas.MenuItem])
def get_menu(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return db.query(MenuItem).offset(skip).limit(limit).all()
