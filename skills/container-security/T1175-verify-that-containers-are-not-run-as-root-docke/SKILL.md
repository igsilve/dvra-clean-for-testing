---
name: t1175-verify-that-containers-are-not-run-as-root-docker
description: Drop root before the application runs and remove the passwordless sudo grant that lets the runtime user regain it.
---

# T1175: Verify that containers are not run as root (Docker)

**Category:** CODE_FIX
**SD Elements:** [T1175](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1175/)
**Priority:** 9

**Finding:** A non-root user is created only after a sudoers rule granting passwordless sudo is installed, so the container user can regain root.

**Code to Fix:**
```dockerfile
# Dockerfile lines 20-25
RUN echo 'ALL ALL=(ALL) NOPASSWD: /usr/bin/find' | sudo tee /etc/sudoers.d/find_nopasswd > /dev/null

RUN useradd -m app
RUN chown app .
USER app
```

**Required Fix:**
```dockerfile
# Dockerfile
FROM python:3.10-slim-bookworm AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 app
COPY --from=builder --chown=app:app /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app app ./app
WORKDIR /app
USER 10001
```

**Success Criteria:**
- The sudoers rule and the sudo package are gone from the image.
- `docker run --rm <image> id -u` prints a non-zero uid.
- The compose service sets `user: "10001:10001"` as well.

**Status:** Applied
