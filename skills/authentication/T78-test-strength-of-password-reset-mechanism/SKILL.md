---
name: t78-test-strength-of-password-reset-mechanism
description: Harden the reset flow: limit verification attempts, rate-limit the endpoint and compare the code in constant time.
---

# T78: Test strength of password reset mechanism

**Category:** CODE_FIX
**SD Elements:** [T78](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T78/)
**Priority:** 9

**Finding:** The reset code is compared with no attempt limit and no rate limiting, so the four-digit code is brute-forceable within its fifteen-minute window.

**Code to Fix:**
```python
# app/apis/auth/services/reset_password_new_password_service.py lines 36-46
    if datetime.now() > user.reset_password_code_expiry_date:
        raise HTTPException(
            status_code=400,
            detail="Reset password code expired!",
        )

    if user.reset_password_code != data.reset_password_code:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset password code",
        )
```

**Required Fix:**
```python
# app/apis/auth/services/reset_password_new_password_service.py
@limiter.limit("5/hour")
def set_new_password(request: Request, data: NewPasswordData, db: Session = Depends(get_db)):
    ...
    user.reset_password_attempts = (user.reset_password_attempts or 0) + 1
    if user.reset_password_attempts > MAX_ATTEMPTS:
        user.reset_password_code = None
        db.add(user); db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset request")

    if not secrets.compare_digest(user.reset_password_code, data.reset_password_code):
        db.add(user); db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset request")
```

**Success Criteria:**
- The code is invalidated after a bounded number of failed attempts.
- The endpoint is rate-limited per account and per source.
- Comparison is constant time and error messages do not distinguish failure causes.

**Status:** Applied
