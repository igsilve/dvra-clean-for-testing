---
name: t4451-test-access-controls-bash-shell
description: Prove with a test that the teardown script refuses an unauthorized caller.
---

# T4451: Test access controls (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4451](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4451/)
**Priority:** 8

**Finding:** There is no access-control logic in the script to exercise.

**Code to Fix:**
```bash
# stop_app.sh lines 1-3
#!/bin/bash

docker compose down
```

**Required Fix:**
```bash
# app/tests/security/test_ops_scripts.sh
unset SDE_DEPLOY_ROLE
if ./stop_app.sh >/dev/null 2>&1; then
    echo "FAIL: stop_app.sh ran without authorization" >&2
    exit 1
fi
```

**Success Criteria:**
- A test asserts a non-zero exit when the role variable is absent.
- The test is wired into CI.

**Status:** Applied
