from apis.auth.utils import get_current_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/restrict-processing", status_code=200)
def restrict_processing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GDPR Art. 18: User requests restriction of processing."""
    current_user.restricted_processing = True
    db.add(current_user)
    db.commit()
    return {"detail": "Processing restricted. Your data will not be used for profiling or automated decision-making."}
