---
name: t1203-test-if-container-cpu-priority-is-appropriately-set-docker
description: Set an explicit CPU allocation so one container cannot starve the others.
---

# T1203: Test if container CPU priority is appropriately set (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1203](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1203/)
**Priority:** 8

**Finding:** Neither cpu_shares nor cpus is set, so the container competes for host CPU without bound.

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
    cpus: 2.0
    cpu_shares: 1024
  db:
    cpus: 1.0
    cpu_shares: 512
```

**Success Criteria:**
- Each service declares an explicit CPU limit or share.
- `docker inspect` reports a non-zero NanoCpus or CpuShares.

**Status:** Applied
