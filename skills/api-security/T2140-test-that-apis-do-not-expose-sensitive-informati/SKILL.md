---
name: t2140-test-that-apis-do-not-expose-sensitive-information
description: Stop returning process environment, filesystem and path information through the API.
---

# T2140: Test that APIs do not expose sensitive information

**Category:** CODE_FIX
**SD Elements:** [T2140](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2140/)
**Priority:** 7

**Finding:** The debug response embeds the full process environment plus the working directory, sys.path and a directory listing, exposing internal configuration and secrets through an API.

**Code to Fix:**
```python
# app/apis/debug/services/get_debug_info_service.py lines 22-27
    env_vars = dict(os.environ)
    local_paths = {
        "current_working_directory": os.getcwd(),
        "sys_path": sys.path,
        "cwd_listing": os.listdir(os.getcwd()),
    }
```

**Required Fix:**
```python
# app/apis/debug/services/get_debug_info_service.py
# Remove the endpoint entirely. If an operational probe is required,
# expose only non-identifying liveness data and require an authenticated
# operator role:

@router.get("/internal/status", status_code=status.HTTP_200_OK)
def get_status(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
):
    return {"status": "ok"}
```

**Success Criteria:**
- No route returns `os.environ`, `sys.path`, `os.getcwd()` or a directory listing.
- An unauthenticated request to any diagnostic path returns 401 or 404.

**Status:** Applied
