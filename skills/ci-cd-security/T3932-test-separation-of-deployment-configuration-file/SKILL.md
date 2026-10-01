---
name: t3932-test-separation-of-deployment-configuration-files-github
description: Add a check that fails the pipeline when deployment configuration or secrets appear in the repository.
---

# T3932: Test separation of deployment configuration files (GitHub)

**Category:** CODE_FIX
**SD Elements:** [T3932](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3932/)
**Priority:** 8

**Finding:** There is a single committed compose file holding environment values, so separation cannot be verified.

**Code to Fix:**
```yaml
# docker-compose.yml lines 15-20
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
      - POSTGRES_SERVER=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=restaurant
```

**Required Fix:**
```yaml
# .github/workflows/ci.yml
      - name: Block committed deployment config and secrets
        run: |
          set -euo pipefail
          if git ls-files | grep -E '(^|/)\.env$|(^|/)deploy/.*\.env$'; then
            echo "Committed environment file detected" >&2; exit 1
          fi
          grep -nE 'POSTGRES_PASSWORD=' docker-compose.yml && exit 1 || true
```

**Success Criteria:**
- The pipeline fails when an environment file is committed.
- The pipeline fails when a credential literal appears in compose or Dockerfile.

**Status:** Applied
