---
name: t4750-isolate-container-networks
description: Segment the services onto declared networks so the database is not reachable from outside the application tier.
---

# T4750: Isolate container networks

**Category:** CODE_FIX
**SD Elements:** [T4750](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4750/)
**Priority:** 10

**Finding:** No user-defined network is declared, so web and db share the default bridge with no segmentation.

**Code to Fix:**
```yaml
# docker-compose.yml lines 1-20
services:
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
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
      - POSTGRES_SERVER=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=restaurant
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
- The database attaches only to an internal network.
- No service uses the default bridge network.
- A container outside the backend network cannot reach port 5432.

**Status:** Applied
