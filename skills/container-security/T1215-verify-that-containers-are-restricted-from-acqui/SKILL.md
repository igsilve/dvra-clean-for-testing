---
name: t1215-verify-that-containers-are-restricted-from-acquiring-addit
description: Prevent privilege escalation inside the container.
---

# T1215: Verify that containers are restricted from acquiring additional privileges (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1215](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1215/)
**Priority:** 8

**Finding:** no-new-privileges is not set in security_opt, and privileged mode would override it.

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
      - no-new-privileges:true
    cap_drop: [ALL]
```

**Success Criteria:**
- `no-new-privileges:true` is set and privileged mode is off.
- A setuid binary inside the container cannot raise privileges.

**Status:** Applied
