---
name: t1213-verify-that-cgroup-usage-is-confirmed-docker
description: Remove privileged mode and SYS_ADMIN so the container cannot reconfigure cgroups, and confirm the cgroup parent.
---

# T1213: Verify that cgroup usage is confirmed (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1213](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1213/)
**Priority:** 7

**Finding:** Running privileged with SYS_ADMIN gives the container control over cgroup configuration.

**Code to Fix:**
```yaml
# docker-compose.yml lines 12-14
    privileged: true
    cap_add:
      - SYS_ADMIN
```

**Required Fix:**
```yaml
# docker-compose.yml
  web:
    privileged: false
    cap_drop: [ALL]
    cgroup_parent: /restaurant.slice
```

**Success Criteria:**
- SYS_ADMIN is not granted to any container.
- The cgroup parent is set explicitly and limits are enforced by it.

**Status:** Applied
