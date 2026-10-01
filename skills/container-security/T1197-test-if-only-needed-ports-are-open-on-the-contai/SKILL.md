---
name: t1197-test-if-only-needed-ports-are-open-on-the-containers-docke
description: Publish the application port only on the interface that needs it, and expose nothing else.
---

# T1197: Test if only needed ports are open on the containers (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1197](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1197/)
**Priority:** 8

**Finding:** Port 8091 is published to all host interfaces with no bind address restriction.

**Code to Fix:**
```yaml
# docker-compose.yml lines 7-8
    ports:
      - 8091:8091
```

**Required Fix:**
```yaml
# docker-compose.yml
  web:
    expose:
      - 8091            # reachable only inside the compose network
  proxy:
    ports:
      - "127.0.0.1:8443:8443"
```

**Success Criteria:**
- No container publishes a port on 0.0.0.0.
- The database port is reachable only from the application service.
- `docker compose ps` shows exactly one published port.

**Status:** Applied
