---
name: t4450-test-authentication-bash-shell
description: Exercise the script's authentication guard so an unauthorized invocation is proven to fail.
---

# T4450: Test authentication (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4450](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4450/)
**Priority:** 8

**Finding:** There is no authentication step in the operational scripts to exercise.

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

unset SDE_DEPLOY_ROLE
if ./start_app.sh >/dev/null 2>&1; then
    echo "FAIL: start_app.sh ran without an operator identity" >&2
    exit 1
fi
echo "PASS: start_app.sh refused an unauthenticated invocation"
```

**Success Criteria:**
- A test invokes the script without credentials and asserts a non-zero exit.
- The test runs in CI alongside the Python suite.

**Status:** Applied
