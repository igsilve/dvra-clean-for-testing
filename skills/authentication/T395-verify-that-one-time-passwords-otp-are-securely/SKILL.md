---
name: t395-verify-that-one-time-passwords-otp-are-securely-used
description: Lengthen the one-time code, limit verification attempts and invalidate the code after use or after too many failures.
---

# T395: Verify that one-time passwords (OTP) are securely used

**Category:** CODE_FIX
**SD Elements:** [T395](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T395/)
**Priority:** 7

**Finding:** The one-time reset code is only four decimal digits and its delivery is not tied to any attempt counter.

**Code to Fix:**
```python
# app/apis/auth/utils/text_code_utils.py lines 10-17
def generate_and_send_code_to_user(user: User, db: Session):
    user.reset_password_code = "".join([str(secrets.randbelow(10)) for _ in range(4)])
    user.reset_password_code_expiry_date = datetime.now() + timedelta(minutes=15)
    db.add(user)
    db.commit()

    success = send_code_to_phone_number(user.phone_number, user.reset_password_code)
    return success
```

**Required Fix:**
```python
# app/apis/auth/utils/text_code_utils.py
CODE_LENGTH = 8
MAX_ATTEMPTS = 5


def generate_and_send_code_to_user(user: User, db: Session):
    user.reset_password_code = "".join(str(secrets.randbelow(10)) for _ in range(CODE_LENGTH))
    user.reset_password_code_expiry_date = datetime.now(timezone.utc) + timedelta(minutes=10)
    user.reset_password_attempts = 0
    db.add(user)
    db.commit()
    return send_code_to_phone_number(user.phone_number, user.reset_password_code)
```

**Success Criteria:**
- The code has at least eight digits of entropy.
- Verification attempts are counted and the code is destroyed after the limit.
- The code is compared with a constant-time function and cleared on success.

**Status:** Applied
