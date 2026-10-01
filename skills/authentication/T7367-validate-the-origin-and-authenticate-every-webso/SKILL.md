---
name: t7367-validate-the-origin-and-authenticate-every-websocket-hands
description: If WebSocket routes are introduced, validate the handshake Origin and authenticate the connection before accepting it.
---

# T7367: Validate the Origin and authenticate every WebSocket handshake (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7367](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7367/)
**Priority:** 9

**Finding:** No WebSocket route is registered and no handshake origin/authentication policy exists for future ones.

**Code to Fix:**
```python
# app/apis/router.py lines 12-22
api_router = APIRouter()
api_router.include_router(healthcheck_router, prefix="", tags=["healthcheck"])
api_router.include_router(
    debug_router, prefix="", tags=["debug"], include_in_schema=False
)
api_router.include_router(menu_router, prefix="", tags=["menu"])
api_router.include_router(orders_router, prefix="", tags=["orders"])
api_router.include_router(auth_router, prefix="", tags=["auth"])
api_router.include_router(admin_router, prefix="", tags=["admin"])
api_router.include_router(users_router, prefix="", tags=["users"])
api_router.include_router(referrals_router, prefix="", tags=["referrals"])
```

**Required Fix:**
```python
# app/apis/<feature>/ws.py
@router.websocket("/ws/orders")
async def order_updates(websocket: WebSocket, db: Session = Depends(get_db)):
    if websocket.headers.get("origin") not in settings.ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    user = await authenticate_websocket(websocket, db)   # validates the bearer token
    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()
```

**Success Criteria:**
- Every WebSocket route checks Origin against the allow-list before accept().
- The connection is authenticated before any message is processed.
- A handshake from a foreign origin is closed with 1008.

**Status:** Applied
