from typing import Literal

from apis.admin.schemas import DiskUsage
from apis.admin.utils import get_disk_usage
from apis.auth.utils import RolesBasedAuthChecker
from db.models import UserRole
from fastapi import APIRouter, Depends, Request, status
from rate_limiting import limiter
from typing_extensions import Annotated

router = APIRouter()

# The mount point is chosen from a fixed set rather than accepted as free
# text, so the endpoint cannot be used to probe arbitrary filesystem paths.
# An unlisted value is rejected by FastAPI with 422 before the handler runs.
MountPoint = Literal["/", "/var", "/tmp"]


@router.get(
    "/admin/stats/disk", response_model=DiskUsage, status_code=status.HTTP_200_OK
)
@limiter.limit("10/minute")
def get_disk_usage_stats(
    request: Request,
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    mount_point: MountPoint = "/",
):
    usage = get_disk_usage(mount_point)
    return DiskUsage(output=usage)
