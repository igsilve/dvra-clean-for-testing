---
name: t1199-test-that-the-host-s-network-namespace-is-not-shared-docke
description: Declare an explicit user-defined network so the container never inherits host or default namespace settings.
---

# T1199: Test that the host's network namespace is not shared (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1199](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1199/)
**Priority:** 8

**Finding:** The service definition relies on default networking with no explicit network mode declared or pinned.

**Code to Fix:**
```yaml
# docker-compose.yml lines 2-8
  web:
    build: .
    command: bash -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8091 --workers 1 --reload"
    volumes:
      - ./app/:/app/
    ports:
      - 8091:8091
```

**Required Fix:**
```yaml
# docker-compose.yml
services:
  web:
    networks: [frontend, backend]
  db:
    networks: [backend]

networks:
  frontend:
  backend:
    internal: true
```

**Success Criteria:**
- `network_mode: host` appears nowhere.
- Services attach to declared networks and the database network is internal.

**Status:** Applied
