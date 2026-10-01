---
name: t1195-test-if-ssh-is-running-within-containers-docker
description: Remove interactive and administrative tooling from the runtime image so no shell service can be started inside the container.
---

# T1195: Test if SSH is running within containers (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1195](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1195/)
**Priority:** 8

**Finding:** The runtime image installs interactive tooling (vim, sudo, gcc) that expands the in-container administrative surface.

**Code to Fix:**
```dockerfile
# Dockerfile lines 12-14
RUN apt-get update
RUN apt-get -y install libpq-dev gcc vim sudo
```

**Required Fix:**
```dockerfile
# Dockerfile
FROM python:3.10-slim-bookworm AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*
# gcc, vim and sudo are build-stage or development concerns and are not installed here.
```

**Success Criteria:**
- The runtime image contains no sshd, sudo, vim or compiler.
- `docker run --rm <image> sh -c 'command -v sshd sudo vim gcc'` finds nothing.

**Status:** Applied
