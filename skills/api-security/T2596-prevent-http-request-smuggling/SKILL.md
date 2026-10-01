---
name: t2596-prevent-http-request-smuggling
description: Terminate client connections on a hardened reverse proxy that normalizes Content-Length and Transfer-Encoding before requests reach the application server.
---

# T2596: Prevent HTTP Request Smuggling

**Category:** CODE_FIX
**SD Elements:** [T2596](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2596/)
**Priority:** 9

**Finding:** Uvicorn is published directly on port 8091 with no hardened reverse proxy in front, so conflicting Content-Length/Transfer-Encoding handling between hops is never normalized.

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
  web:
    build: .
    command: uvicorn main:app --host 127.0.0.1 --port 8091 --workers 4
    expose:
      - 8091
  proxy:
    image: nginx:1.27-alpine
    depends_on: [web]
    ports:
      - "127.0.0.1:8443:8443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf:ro
    # nginx.conf: proxy_http_version 1.1; drops requests carrying both
    # Content-Length and Transfer-Encoding, and rejects malformed framing.
```

**Success Criteria:**
- The application server is not directly reachable from outside the container network.
- A request carrying both Content-Length and Transfer-Encoding headers is rejected at the edge.
- Front-end and back-end agree on HTTP version and keep-alive handling.

**Status:** Applied
