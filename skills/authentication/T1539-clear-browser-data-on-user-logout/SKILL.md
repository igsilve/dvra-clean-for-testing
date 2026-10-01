---
name: t1539-clear-browser-data-on-user-logout
description: Provide a logout endpoint that invalidates the issued token server side and instructs the client to clear it.
---

# T1539: Clear browser data on user logout

**Category:** CODE_FIX
**SD Elements:** [T1539](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1539/)
**Priority:** 8

**Finding:** The auth router registers no logout route, so there is nothing that invalidates the token or instructs the client to clear stored credentials.

**Code to Fix:**
```python
# app/apis/auth/service.py lines 12-19
router = APIRouter()
router.include_router(get_profile_router)
router.include_router(get_token_router)
router.include_router(register_user_router)
router.include_router(update_profile_router)
router.include_router(patch_profile_router)
router.include_router(reset_password_router)
router.include_router(reset_password_new_password_router)
```

**Required Fix:**
```python
# app/apis/auth/services/logout_service.py
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
    response: Response,
    db: Session = Depends(get_db),
):
    db.add(RevokedToken(jti=decode_jti(token), revoked_at=datetime.now(timezone.utc)))
    db.commit()
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")
```

**Success Criteria:**
- A /logout route exists and is registered on the auth router.
- A token presented after logout is rejected with 401.
- Authentication cookies are cleared in the logout response.

**Status:** Applied
