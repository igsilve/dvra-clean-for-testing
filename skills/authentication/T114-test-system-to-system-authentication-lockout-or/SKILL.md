---
name: t114-test-system-to-system-authentication-lockout-or-throttling
description: Throttle and lock out repeated failed authentications, including those from machine accounts.
---

# T114: Test system-to-system authentication lockout or throttling

**Category:** CODE_FIX
**SD Elements:** [T114](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T114/)
**Priority:** 8

**Finding:** Failed authentications are returned immediately with no counter, lockout or backoff for machine accounts.

**Code to Fix:**
```python
# app/apis/auth/services/get_token_service.py lines 16-27
@router.post("/token")
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**Required Fix:**
```python
# app/apis/auth/utils/utils.py
MAX_FAILURES = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def authenticate_user(db, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return False
    if not verify_password(password, user.password):
        user.failed_logins = (user.failed_logins or 0) + 1
        if user.failed_logins >= MAX_FAILURES:
            user.locked_until = datetime.now(timezone.utc) + LOCKOUT_WINDOW
        db.add(user); db.commit()
        return False
    user.failed_logins = 0
    user.locked_until = None
    db.add(user); db.commit()
    return user
```

**Success Criteria:**
- Consecutive failures are counted per account and persisted.
- The account stops authenticating once the threshold is reached, for the configured window.
- A successful authentication resets the counter.
- The response is identical whether the account is locked or the password was simply wrong.

**Status:** Applied
