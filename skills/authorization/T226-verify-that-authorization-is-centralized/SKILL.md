---
name: t226-verify-that-authorization-is-centralized
description: Replace the inline role comparison in the handler with the shared authorization dependency.
---

# T226: Verify that authorization is centralized

**Category:** CODE_FIX
**SD Elements:** [T226](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T226/)
**Priority:** 9

**Finding:** The role check is written inline in the handler instead of going through the shared authorization dependency.

**Code to Fix:**
```python
# app/apis/admin/services/get_disk_stats_service.py lines 21-24
    if current_user.role != UserRole.CHEF.value:
        raise HTTPException(
            status_code=403, detail="Only Chef is authorized to get current disk stats!"
        )
```

**Required Fix:**
```python
# app/apis/admin/services/get_disk_stats_service.py
@router.get("/admin/stats/disk", response_model=DiskUsage, status_code=status.HTTP_200_OK)
def get_disk_usage_stats(
    _: Annotated[User, Depends(Requires(Permission.READ_DISK_STATS))],
    mount_point: MountPoint = MountPoint.ROOT,
):
    return DiskUsage(output=get_disk_usage(mount_point.value))
```

**Success Criteria:**
- The handler contains no `if current_user.role != ...` comparison.
- A repository-wide search finds role comparisons only inside the authorization module.

**Status:** Applied
