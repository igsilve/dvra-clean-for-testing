---
name: t98-test-for-input-validation-on-a-server
description: Validate the request parameter on the server against a closed set before it reaches any downstream call.
---

# T98: Test for input validation on a server

**Category:** CODE_FIX
**SD Elements:** [T98](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T98/)
**Priority:** 7

**Finding:** The `parameters` query string is accepted with no validation and handed to a shell command builder.

**Code to Fix:**
```python
# app/apis/admin/services/get_disk_stats_service.py lines 16-27
def get_disk_usage_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    parameters: str = "",
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.CHEF.value:
        raise HTTPException(
            status_code=403, detail="Only Chef is authorized to get current disk stats!"
        )

    usage = get_disk_usage(parameters)
    return DiskUsage(output=usage)
```

**Required Fix:**
```python
# app/apis/admin/services/get_disk_stats_service.py
@router.get("/admin/stats/disk", response_model=DiskUsage, status_code=status.HTTP_200_OK)
def get_disk_usage_stats(
    _: Annotated[User, Depends(Requires(Permission.READ_DISK_STATS))],
    mount_point: MountPoint = MountPoint.ROOT,     # enum: FastAPI rejects anything else with 422
):
    return DiskUsage(output=get_disk_usage(mount_point))
```

**Success Criteria:**
- The parameter is typed as an enum or carries an explicit pattern and length constraint.
- Validation happens server side and does not rely on the client.
- An out-of-set value returns 422 before the handler body runs.

**Status:** Applied
