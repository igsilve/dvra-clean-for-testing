from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthcheckResponse(BaseModel):
    ok: bool


@router.get("/healthcheck", response_model=HealthcheckResponse)
def healthcheck():
    # The response carries no version or runtime details: an unauthenticated
    # liveness probe must not help an attacker fingerprint the stack.
    return HealthcheckResponse(ok=True)
