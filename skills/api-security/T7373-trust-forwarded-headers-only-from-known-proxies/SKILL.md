---
name: t7373-trust-forwarded-headers-only-from-known-proxies-behind-tls
description: Derive the client address from forwarded headers only when the request arrives from a known proxy, and never make an authorization decision on it alone.
---

# T7373: Trust forwarded headers only from known proxies behind TLS (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7373](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7373/)
**Priority:** 10

**Finding:** Authorization is decided from request.client.host alone, with no proxy allow-list and no validation of forwarded headers.

**Code to Fix:**
```python
# app/apis/admin/services/reset_chef_password_service.py lines 22-28
    client_host = request.client.host

    if client_host != "127.0.0.1":
        raise HTTPException(
            status_code=403,
            detail="Chef password can be reseted only from the local machine!",
        )
```

**Required Fix:**
```python
# app/apis/admin/services/reset_chef_password_service.py
# Replace the address check with a real authorization decision:
@router.post("/admin/reset-chef-password", include_in_schema=False)
def reset_chef_password(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    db: Session = Depends(get_db),
):
    ...

# and run uvicorn with --proxy-headers --forwarded-allow-ips <proxy-cidr>
# so request.client.host is only rewritten for traffic from that proxy.
```

**Success Criteria:**
- No route grants access based on request.client.host or an X-Forwarded-For value.
- Forwarded headers are honoured only for source addresses in the configured proxy range.

**Status:** Applied
