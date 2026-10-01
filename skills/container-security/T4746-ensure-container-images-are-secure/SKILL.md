---
name: t4746-ensure-container-images-are-secure
description: Pin both base images by digest and verify their provenance before use.
---

# T4746: Ensure container images are secure

**Category:** CODE_FIX
**SD Elements:** [T4746](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4746/)
**Priority:** 10

**Finding:** Both stages reference floating tags (python:3.10-bookworm, python:3.10-slim-bookworm) with no digest pinning or provenance verification.

**Code to Fix:**
```dockerfile
# Dockerfile lines 1-10
FROM python:3.10-bookworm as builder

RUN pip install poetry==1.4.2
WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.10-slim-bookworm as runtime
```

**Required Fix:**
```dockerfile
# Dockerfile
FROM python:3.10-bookworm@sha256:<builder-digest> AS builder
...
FROM python:3.10-slim-bookworm@sha256:<runtime-digest> AS runtime
# The digests are recorded in deploy/base-images.lock and refreshed by a
# scheduled job that re-runs the vulnerability scan before promoting a change.
```

**Success Criteria:**
- Both FROM lines reference an immutable digest.
- Digest updates go through the same review and scan as code changes.
- The image signature is verified before the build proceeds.

**Status:** Applied
