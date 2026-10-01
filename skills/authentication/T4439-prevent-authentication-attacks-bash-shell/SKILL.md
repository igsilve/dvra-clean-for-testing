---
name: t4439-prevent-authentication-attacks-bash-shell
description: Require an explicit, verified operator identity before the deployment scripts perform privileged actions.
---

# T4439: Prevent authentication attacks (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4439](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4439/)
**Priority:** 8

**Finding:** The startup script invokes docker compose with no authentication or identity check on the caller.

**Code to Fix:**
```bash
# start_app.sh lines 1-4
#!/bin/bash

mkdir -p postgres_data
docker compose up $1
```

**Required Fix:**
```bash
#!/bin/bash
# start_app.sh
set -euo pipefail

if [ "${SDE_DEPLOY_ROLE:-}" != "operator" ]; then
    echo "start_app.sh must be run by an authorized operator" >&2
    exit 1
fi

mkdir -m 0750 -p postgres_data
docker compose up "$@"
```

**Success Criteria:**
- The script fails closed when the operator identity is absent.
- `set -euo pipefail` is present so a failed check aborts the script.

**Status:** Applied
