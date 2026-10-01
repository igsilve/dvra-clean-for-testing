---
name: t4440-enforce-access-controls-bash-shell
description: Gate the privileged teardown action behind an explicit authorization check.
---

# T4440: Enforce access controls (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4440](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4440/)
**Priority:** 8

**Finding:** The teardown script performs a privileged compose action with no access control on who may run it.

**Code to Fix:**
```bash
# stop_app.sh lines 1-3
#!/bin/bash

docker compose down
```

**Required Fix:**
```bash
#!/bin/bash
# stop_app.sh
set -euo pipefail

if [ "${SDE_DEPLOY_ROLE:-}" != "operator" ]; then
    echo "stop_app.sh requires the operator role" >&2
    exit 1
fi

docker compose down
```

**Success Criteria:**
- The script exits non-zero when the caller is not authorized.
- `set -euo pipefail` prevents the compose command from running after a failed check.

**Status:** Applied
