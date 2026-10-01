---
name: t7415-verify-that-dangerous-functionality-and-risky-third-party
description: Confirm the isolation boundary around the component that executes shell commands.
---

# T7415: Verify that dangerous functionality and risky third-party components are isolated via sandboxing or encapsulation

**Category:** CODE_FIX
**SD Elements:** [T7415](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7415/)
**Priority:** 9

**Finding:** The container that executes shell commands on request runs privileged with SYS_ADMIN, so nothing is isolated.

**Code to Fix:**
```yaml
# docker-compose.yml lines 12-14
    privileged: true
    cap_add:
      - SYS_ADMIN
```

**Required Fix:**
```yaml
# app/tests/security/test_container_isolation.sh
set -euo pipefail

docker compose config | grep -q 'privileged: true' && { echo "FAIL: privileged" >&2; exit 1; }
docker compose config | grep -q 'SYS_ADMIN'       && { echo "FAIL: SYS_ADMIN" >&2; exit 1; }
docker compose exec -T web id -u | grep -qv '^0$' || { echo "FAIL: running as root" >&2; exit 1; }
```

**Success Criteria:**
- A check fails when privileged mode or SYS_ADMIN is present in the rendered compose config.
- The application container runs as a non-root user with a read-only root filesystem.

**Status:** Applied
