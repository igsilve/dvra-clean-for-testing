---
name: t1211-verify-that-seccomp-profile-is-enabled-docker
description: Drop privileged mode so the default seccomp profile applies, and pin the profile explicitly.
---

# T1211: Verify that seccomp profile is enabled (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1211](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1211/)
**Priority:** 8

**Finding:** privileged: true disables the default seccomp profile for the container.

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
    security_opt:
      - seccomp=./deploy/seccomp-restaurant.json
      - no-new-privileges:true
```

**Success Criteria:**
- `privileged: true` appears nowhere.
- A seccomp profile is referenced explicitly rather than relying on the default.
- `docker inspect` shows SeccompProfile applied.

**Status:** Applied
