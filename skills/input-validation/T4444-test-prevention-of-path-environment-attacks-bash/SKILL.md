---
name: t4444-test-prevention-of-path-environment-attacks-bash-shell
description: Add a check that the scripts cannot be redirected through a hostile PATH.
---

# T4444: Test prevention of path environment attacks (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4444](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4444/)
**Priority:** 7

**Finding:** There is no PATH hardening in the script to exercise.

**Code to Fix:**
```bash
# start_app.sh lines 1-4
#!/bin/bash

mkdir -p postgres_data
docker compose up $1
```

**Required Fix:**
```bash
# app/tests/security/test_ops_scripts.sh
set -euo pipefail

TMP="$(mktemp -d)"
printf '#!/bin/sh\necho HIJACKED\n' > "$TMP/docker"
chmod +x "$TMP/docker"

output="$(PATH="$TMP:$PATH" SDE_DEPLOY_ROLE=operator ./start_app.sh 2>&1 || true)"
case "$output" in
    *HIJACKED*) echo "FAIL: PATH hijack succeeded" >&2; exit 1 ;;
esac
```

**Success Criteria:**
- A test plants a shadowing binary on PATH and asserts it is not executed.
- The test runs in CI.

**Status:** Applied
