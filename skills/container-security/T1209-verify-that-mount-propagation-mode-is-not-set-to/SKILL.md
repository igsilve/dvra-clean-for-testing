---
name: t1209-verify-that-mount-propagation-mode-is-not-set-to-shared-do
description: Express mounts in long form and pin propagation to a non-shared mode.
---

# T1209: Verify that mount propagation mode is not set to 'shared' (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1209](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1209/)
**Priority:** 7

**Finding:** The bind mount is declared in short-string form, so propagation mode is neither stated nor constrained.

**Code to Fix:**
```yaml
# docker-compose.yml lines 5-6
    volumes:
      - ./app/:/app/
```

**Required Fix:**
```yaml
# docker-compose.yml
  web:
    volumes:
      - type: bind
        source: ./deploy/nginx.conf
        target: /etc/nginx/nginx.conf
        read_only: true
        bind:
          propagation: rprivate
```

**Success Criteria:**
- No mount uses `shared` or `rshared` propagation.
- Every bind mount is declared in long form with an explicit propagation value.
- `docker compose config` shows no shared propagation.

**Status:** Applied
