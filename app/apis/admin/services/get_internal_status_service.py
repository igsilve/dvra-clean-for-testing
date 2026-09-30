"""Operator liveness view.

This replaced a `/debug` endpoint that returned os.environ, sys.path and a
working-directory listing to anonymous callers. What is left is the part
operations genuinely needs -- is it up, and which build -- behind the same
role as every other administrative route.

It lives under `admin` rather than in a package of its own. The previous
router was mounted with include_in_schema=False, and a router nobody can see
is where the next introspection route gets added without anyone noticing it
is there; the route-table guard test cannot report what the schema omits.
"""

from apis.auth.utils import Permission, Requires
from config import settings
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing_extensions import Annotated

router = APIRouter()


class StatusResponse(BaseModel):
    """Two fields, and the response_model is what enforces that.

    Returning a dict here would let a later edit add a field that happens to
    be in scope -- a settings object, an exception -- and it would be
    serialised without anyone choosing to expose it.
    """

    status: str
    version: str


@router.get(
    "/internal/status",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_internal_status(
    _: Annotated[bool, Depends(Requires(Permission.READ_DEBUG_INFO))],
):
    return StatusResponse(status="ok", version=settings.VERSION)
