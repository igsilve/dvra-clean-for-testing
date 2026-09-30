from typing import List

from apis.menu import schemas
from db.models import MenuItem
from db.result_limits import fetch_bounded
from db.session import get_db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class MenuResponse(BaseModel):
    """Object envelope rather than a bare array.

    A top-level JSON array is script-includable, so wrapping it keeps the
    payload from being readable if this endpoint is ever loaded via a
    `<script src=...>` tag.
    """

    items: List[schemas.MenuItem]


@router.get("/menu", response_model=MenuResponse)
def get_menu(db: Session = Depends(get_db)):
    return MenuResponse(items=fetch_bounded(db.query(MenuItem)))
