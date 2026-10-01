---
name: t7375-keep-blocking-work-off-the-async-event-loop-fastapi
description: Keep blocking password hashing and database work off the event loop by declaring the handler synchronous or offloading the blocking call.
---

# T7375: Keep blocking work off the async event loop (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7375](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7375/)
**Priority:** 8

**Finding:** The handler is declared `async def` but calls create_user, which performs a blocking bcrypt hash and synchronous database work directly on the event loop.

**Code to Fix:**
```python
# app/apis/auth/services/register_user_service.py lines 19-40
async def register_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    auth = request.headers.get("Authorization")

    if auth:
        raise HTTPException(
            status_code=400,
            detail="You're already logged in. You can not register an account.",
        )

    try:
        db_user = create_user(
            db,
            user.username,
            user.password,
            user.first_name,
            user.last_name,
            user.phone_number,
        )
```

**Required Fix:**
```python
# app/apis/auth/services/register_user_service.py
# Declaring the handler `def` lets FastAPI run it in the threadpool:
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    ...

# If the route must stay async, offload the blocking part:
#   db_user = await run_in_threadpool(create_user, db, user.username, ...)
```

**Success Criteria:**
- No `async def` handler calls passlib hashing or a synchronous SQLAlchemy query directly.
- Concurrent registrations do not block unrelated requests.

**Status:** Applied
