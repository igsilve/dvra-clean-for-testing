---
name: t4454-test-cryptographic-functions-bash-shell
description: Add a check that the operational scripts handle no plaintext key material.
---

# T4454: Test cryptographic functions (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4454](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4454/)
**Priority:** 8

**Finding:** There are no cryptographic functions in the shell tooling to exercise.

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

if grep -nE '(PASSWORD|SECRET|TOKEN|KEY)=' ./*.sh; then
    echo "FAIL: credential literal found in a shell script" >&2
    exit 1
fi
```

**Success Criteria:**
- A check fails the build when a credential literal appears in a shell script.
- The check runs on every change.

**Status:** Applied
