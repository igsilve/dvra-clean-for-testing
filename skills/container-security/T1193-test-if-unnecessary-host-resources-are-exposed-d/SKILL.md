---
name: t1193-test-if-unnecessary-host-resources-are-exposed-docker
description: Stop bind-mounting the host source tree into the running container.
---

# T1193: Test if unnecessary host resources are exposed (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1193](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1193/)
**Priority:** 8

**Finding:** The host source tree is bind-mounted read-write into the container at /app.

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
    build: .
    # no host bind mount; the image already contains ./app
    tmpfs:
      - /tmp:size=64m,mode=1777
# Keep the bind mount only in a separate docker-compose.override.yml used for
# local development, which is not deployed.
```

**Success Criteria:**
- The deployed compose file mounts no host path into the container.
- Writable paths are explicit tmpfs mounts with size limits.

**Status:** Applied
