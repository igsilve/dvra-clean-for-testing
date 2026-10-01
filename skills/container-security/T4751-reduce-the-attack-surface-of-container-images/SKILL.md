---
name: t4751-reduce-the-attack-surface-of-container-images
description: Strip build tooling and interactive utilities from the runtime image and clean the package cache.
---

# T4751: Reduce the attack surface of container images

**Category:** CODE_FIX
**SD Elements:** [T4751](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4751/)
**Priority:** 10

**Finding:** apt-get installs gcc, vim and sudo into the runtime image and never cleans the apt lists.

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
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
```

**Success Criteria:**
- gcc, vim and sudo are absent from the runtime image.
- `--no-install-recommends` is used and the apt lists are removed in the same layer.
- The runtime image is measurably smaller than before.

**Status:** Applied
