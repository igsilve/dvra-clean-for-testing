---
name: t4747-limit-container-privileges
description: Remove privileged mode and the SYS_ADMIN capability and run with all capabilities dropped.
---

# T4747: Limit container privileges

**Category:** CODE_FIX
**SD Elements:** [T4747](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4747/)
**Priority:** 10

**Finding:** The web container runs privileged and additionally requests the SYS_ADMIN capability.

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
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    user: "10001:10001"
```

**Success Criteria:**
- No service declares `privileged: true` or `cap_add`.
- All capabilities are dropped and only those proven necessary are added back individually.
- The application runs correctly with the reduced capability set.

**Status:** Applied
