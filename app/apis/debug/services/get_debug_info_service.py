from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/debug", include_in_schema=False)
def get_debug_info_service():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
