---
name: t4447-test-directory-writing-and-reading-bash-shell
description: Assert that the directories the scripts create are not group- or world-accessible.
---

# T4447: Test directory writing and reading (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4447](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4447/)
**Priority:** 8

**Finding:** Directory creation applies no explicit mode and no ownership check.

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

rm -rf postgres_data
SDE_DEPLOY_ROLE=operator ./start_app.sh --no-start >/dev/null 2>&1 || true

mode="$(stat -f '%Lp' postgres_data)"
if [ "$mode" != "700" ]; then
    echo "FAIL: postgres_data mode is $mode, expected 700" >&2
    exit 1
fi
```

**Success Criteria:**
- A test asserts the created directory mode is 0700.
- The test fails if the explicit mode is removed.

**Status:** Applied
