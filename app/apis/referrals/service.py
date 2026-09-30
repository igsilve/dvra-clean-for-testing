from typing import List

from apis.auth.schemas import User
from apis.auth.utils import get_current_user
from apis.referrals.schemas import DiscountCouponRead
from apis.referrals.utils import get_referral_code
from db.models import DiscountCoupon
from db.models import User as UserModel
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()

# 20% discount on the first order
# for user applying the referral code
REFERRAL_DISCOUNT_PERCENTAGE = 20


class ReferralCodeResponse(BaseModel):
    code: str


class ApplyReferralRequest(BaseModel):
    referral_code: str


class ApplyReferralResponse(BaseModel):
    message: str
    discount: float


@router.get("/referral-code", response_model=ReferralCodeResponse)
def get_referral_code_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Return the current user's referral code.

    Read-only: generating a code is a state change and therefore lives on the
    POST route below. A GET must stay side-effect free so that a prefetch, a
    link or an image URL cannot provoke a write.
    """
    db_user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if db_user is None or db_user.referral_code is None:
        raise HTTPException(status_code=404, detail="No referral code has been issued")

    return ReferralCodeResponse(code=db_user.referral_code)


@router.post(
    "/referral-code",
    response_model=ReferralCodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_referral_code_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Issue the current user's referral code, or return the existing one."""
    db_user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    code = get_referral_code(db, db_user)

    return ReferralCodeResponse(code=code)


@router.post("/apply-referral", response_model=ApplyReferralResponse)
def apply_referral_code(
    request: ApplyReferralRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Referrals can be applied by users to receive discounts."""
    referrer = (
        db.query(UserModel)
        .filter(UserModel.referral_code == request.referral_code)
        .first()
    )

    if referrer is None:
        return ApplyReferralResponse(message="Invalid referral code", discount=0.0)

    discount_coupon = DiscountCoupon(
        user_id=current_user.id,
        referrer_user_id=referrer.id,
        discount_percentage=REFERRAL_DISCOUNT_PERCENTAGE,
    )
    db.add(discount_coupon)
    db.commit()

    return ApplyReferralResponse(
        message=f"Referral code {request.referral_code} applied successfully",
        discount=REFERRAL_DISCOUNT_PERCENTAGE,
    )


@router.get("/discount-coupons", response_model=List[DiscountCouponRead])
def get_discount_coupons(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Retrieve all discount coupons for the current user."""
    coupons = (
        db.query(DiscountCoupon).filter(DiscountCoupon.user_id == current_user.id).all()
    )
    return coupons
