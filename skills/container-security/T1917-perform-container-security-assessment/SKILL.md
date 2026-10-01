---
name: t1917-perform-container-security-assessment
description: Add an image assessment step that fails the build on the findings this Dockerfile currently introduces.
---

# T1917: Perform container security assessment

**Category:** CODE_FIX
**SD Elements:** [T1917](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1917/)
**Priority:** 10

**Finding:** The runtime stage installs a compiler and sudo and grants a passwordless sudoers rule, none of which is covered by any image assessment step.

**Code to Fix:**
```dockerfile
# Dockerfile lines 10-20
FROM python:3.10-slim-bookworm as runtime

RUN apt-get update
RUN apt-get -y install libpq-dev gcc vim sudo

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
WORKDIR /app

RUN echo 'ALL ALL=(ALL) NOPASSWD: /usr/bin/find' | sudo tee /etc/sudoers.d/find_nopasswd > /dev/null
```

**Required Fix:**
```dockerfile
# .github/workflows/ci.yml
      - name: Scan image
        run: |
          set -euo pipefail
          docker build -t restaurant-api:${{ github.sha }} .
          trivy image --exit-code 1 --severity HIGH,CRITICAL restaurant-api:${{ github.sha }}
          hadolint Dockerfile
          docker run --rm restaurant-api:${{ github.sha }} sh -c '! command -v sudo'
```

**Success Criteria:**
- Every build runs an image vulnerability scan that fails on high and critical findings.
- A Dockerfile linter runs in the same job.
- The assessment output is retained as a build artifact.

**Status:** Applied
