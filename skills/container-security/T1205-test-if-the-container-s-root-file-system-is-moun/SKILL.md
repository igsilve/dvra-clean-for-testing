---
name: t1205-test-if-the-container-s-root-file-system-is-mounted-as-rea
description: Mount the container root filesystem read-only and provide explicit writable tmpfs paths.
---

# T1205: Test if the container's root file system is mounted as read-only (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1205](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1205/)
**Priority:** 8

**Finding:** read_only is not set, so the container root filesystem is writable.

**Code to Fix:**
```yaml
# docker-compose.yml lines 2-14
  web:
    build: .
    command: bash -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8091 --workers 1 --reload"
    volumes:
      - ./app/:/app/
    ports:
      - 8091:8091
    depends_on:
      db:
        condition: service_healthy
    privileged: true
    cap_add:
      - SYS_ADMIN
```

**Required Fix:**
```yaml
# docker-compose.yml
  web:
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
      - /run:size=8m
```

**Success Criteria:**
- `read_only: true` is set on every application service.
- Writing to an unexpected path inside the container fails.
- The application still starts with the read-only root.

**Status:** Applied
