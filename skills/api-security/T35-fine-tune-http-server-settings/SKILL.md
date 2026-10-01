---
name: t35-fine-tune-http-server-settings
description: Run the application server with production settings: no auto-reload, multiple workers and explicit request timeouts and concurrency limits.
---

# T35: Fine-tune HTTP server settings

**Category:** CODE_FIX
**SD Elements:** [T35](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T35/)
**Priority:** 9

**Finding:** The server is started with --reload and a single worker and no request/keep-alive timeouts or concurrency limits configured.

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
    command: >
      uvicorn main:app --host 127.0.0.1 --port 8091
      --workers 4
      --timeout-keep-alive 5
      --limit-concurrency 256
      --limit-max-requests 10000
      --proxy-headers --forwarded-allow-ips 10.0.0.0/8
```

**Success Criteria:**
- `--reload` does not appear in any non-development compose profile.
- Keep-alive, concurrency and max-request limits are set explicitly.
- The server binds to the internal interface only.

**Status:** Applied
