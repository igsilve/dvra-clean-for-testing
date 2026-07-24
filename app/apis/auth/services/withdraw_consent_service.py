from datetime import datetime, timezone

from apis.auth.utils import get_current_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/withdraw-consent", status_code=200)
def withdraw_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GDPR Art. 7(3): User withdraws consent and requests data erasure."""
    current_user.consent_withdrawn = True
    current_user.consent_withdrawn_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()
    return {"detail": "Consent withdrawn. Your personal data will be erased within 30 days."}
