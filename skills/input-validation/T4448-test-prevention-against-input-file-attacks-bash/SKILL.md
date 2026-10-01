---
name: t4448-test-prevention-against-input-file-attacks-bash-shell
description: Test that the script refuses to run when a required input file is missing or not a regular file.
---

# T4448: Test prevention against input file attacks (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4448](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4448/)
**Priority:** 8

**Finding:** Input files consumed by the script are not validated before execution.

**Code to Fix:**
```bash
# start_game.sh lines 1-4
#!/bin/bash

./start_app.sh -d
docker compose exec web python3 game.py
```

**Required Fix:**
```bash
# app/tests/security/test_ops_scripts.sh
set -euo pipefail

mv start_app.sh start_app.sh.bak
if ./start_game.sh >/dev/null 2>&1; then
    echo "FAIL: start_game.sh ran with a missing dependency" >&2
    mv start_app.sh.bak start_app.sh
    exit 1
fi
mv start_app.sh.bak start_app.sh
```

**Success Criteria:**
- A test removes a required input and asserts the script exits non-zero.
- The failure message names the missing file.

**Status:** Applied
