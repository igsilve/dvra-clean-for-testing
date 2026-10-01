---
name: t7382-make-critical-state-changing-operations-replay-resistant-f
description: Make the referral application idempotent so replaying the same request cannot mint additional coupons.
---

# T7382: Make critical state-changing operations replay-resistant (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7382](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7382/)
**Priority:** 7

**Finding:** Applying a referral code creates a new discount coupon every time it is called, with no idempotency key or one-per-user guard, so the request can be replayed for unlimited coupons.

**Code to Fix:**
```python
# app/apis/referrals/service.py lines 47-74
@router.post("/apply-referral", response_model=ApplyReferralResponse)
async def apply_referral_code(
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
```

**Required Fix:**
```python
# app/apis/referrals/service.py
existing = (
    db.query(DiscountCoupon)
    .filter(DiscountCoupon.user_id == current_user.id)
    .first()
)
if existing is not None:
    raise HTTPException(status_code=409, detail="A referral has already been applied to this account")

if referrer.id == current_user.id:
    raise HTTPException(status_code=400, detail="You cannot apply your own referral code")
```

**Success Criteria:**
- Submitting the same referral request twice produces exactly one coupon.
- A user cannot apply their own referral code.
- The uniqueness rule is enforced by a database constraint as well as the handler.

**Status:** Applied
