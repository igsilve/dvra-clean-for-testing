from apis.auth.utils import RolesBasedAuthChecker
from config import settings
from db.models import UserRole
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing_extensions import Annotated

router = APIRouter()


class StatusResponse(BaseModel):
    status: str
    version: str


# The former /debug endpoint returned os.environ, sys.path and a working
# directory listing to anonymous callers. It is replaced by a Chef-only
# liveness view whose response_model allows two non-sensitive fields.
@router.get(
    "/internal/status",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_internal_status(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
):
    return StatusResponse(status="ok", version=settings.VERSION)
