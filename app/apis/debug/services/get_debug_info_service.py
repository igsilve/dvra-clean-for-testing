import os
import platform

import psutil
from apis.auth.utils import get_current_user
from db.models import User, UserRole
from fastapi import APIRouter, Depends, HTTPException, status
from typing_extensions import Annotated

router = APIRouter()


@router.get("/debug", status_code=status.HTTP_200_OK)
def get_debug_info_service(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != UserRole.CHEF.value:
        raise HTTPException(status_code=403, detail="Unauthorized")

    os_info = {
        "system": platform.system(),
        "release": platform.release(),
    }

    disk_usage = psutil.disk_usage(os.getcwd())
    disk_info = {
        "total": disk_usage.total,
        "used": disk_usage.used,
        "free": disk_usage.free,
        "percent": disk_usage.percent,
    }

    mem = psutil.virtual_memory()
    memory_info = {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "free": mem.free,
        "percent": mem.percent,
    }

    debug_info = {
        "os_info": os_info,
        "disk_usage": disk_info,
        "memory_usage": memory_info,
    }

    return debug_info
