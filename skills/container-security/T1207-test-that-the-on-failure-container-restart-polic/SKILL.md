---
name: t1207-test-that-the-on-failure-container-restart-policy-is-set-t
description: Declare a bounded restart policy so a crash-looping container does not restart indefinitely.
---

# T1207: Test that the 'on-failure' container restart policy is set to 5 (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1207](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1207/)
**Priority:** 8

**Finding:** No restart policy is declared for the web service.

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
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 5
        delay: 5s
    # compose v2 standalone equivalent:
    restart: on-failure:5
```

**Success Criteria:**
- The restart policy is on-failure with a bounded attempt count.
- `docker inspect` shows MaximumRetryCount of 5.

**Status:** Applied
