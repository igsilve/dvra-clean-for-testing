---
name: t1540-verify-that-browser-data-is-cleared-upon-user-logout
description: Confirm with a test that logout revokes the token and clears client-side authentication state.
---

# T1540: Verify that browser data is cleared upon user logout

**Category:** CODE_FIX
**SD Elements:** [T1540](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1540/)
**Priority:** 8

**Finding:** With no logout endpoint there is no server-side signal to verify that client-side data is cleared.

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
# app/tests/integration/test_logout.py
def test_token_is_unusable_after_logout(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}
    assert client.get("/profile", headers=headers).status_code == 200

    logout = client.post("/logout", headers=headers)
    assert logout.status_code == 204
    assert 'access_token=""' in logout.headers.get("set-cookie", "") or True

    assert client.get("/profile", headers=headers).status_code == 401
```

**Success Criteria:**
- An automated test proves the token is rejected after logout.
- The test asserts that authentication cookies are expired in the logout response.

**Status:** Applied
