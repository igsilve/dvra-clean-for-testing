---
name: t4442-manage-and-protect-script-processes-bash-shell
description: Supervise the process the script starts: serialize invocations, set a timeout and clean up on exit.
---

# T4442: Manage and protect script processes (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4442](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4442/)
**Priority:** 8

**Finding:** The teardown script starts a privileged process with no process isolation, locking or signal handling.

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

LOCK=/var/lock/restaurant-deploy.lock
exec 9>"$LOCK"
flock -n 9 || { echo "another deploy action is in progress" >&2; exit 1; }

trap 'rm -f "$LOCK"' EXIT

timeout 120 docker compose down
```

**Success Criteria:**
- Concurrent invocations are prevented by a lock.
- The privileged command runs under a timeout.
- A trap cleans up on any exit path.

**Status:** Applied
