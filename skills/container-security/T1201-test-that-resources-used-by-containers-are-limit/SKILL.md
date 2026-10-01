---
name: t1201-test-that-resources-used-by-containers-are-limited-docker
description: Bound the memory, process count and file descriptors each container may consume.
---

# T1201: Test that resources used by containers are limited (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1201](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1201/)
**Priority:** 8

**Finding:** No memory, pids or ulimit constraints are declared for the web service.

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
    mem_limit: 512m
    memswap_limit: 512m
    pids_limit: 200
    ulimits:
      nofile:
        soft: 1024
        hard: 2048
```

**Success Criteria:**
- Memory, pids and file-descriptor limits are declared for every service.
- `docker inspect` shows non-zero Memory and PidsLimit values.

**Status:** Applied
