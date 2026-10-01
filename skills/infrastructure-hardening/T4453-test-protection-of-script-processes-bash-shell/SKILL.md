---
name: t4453-test-protection-of-script-processes-bash-shell
description: Run the spawned process non-interactively under a timeout and ensure it is cleaned up.
---

# T4453: Test protection of script processes (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4453](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4453/)
**Priority:** 8

**Finding:** A second process is launched inside the running container with no supervision, timeout or cleanup.

**Code to Fix:**
```bash
# start_game.sh lines 1-4
#!/bin/bash

./start_app.sh -d
docker compose exec web python3 game.py
```

**Required Fix:**
```bash
#!/bin/bash
# start_game.sh
set -euo pipefail

trap 'docker compose kill web >/dev/null 2>&1 || true' INT TERM

timeout 300 docker compose exec -T web python3 /app/game.py
status=$?
trap - INT TERM
exit "$status"
```

**Success Criteria:**
- The spawned process runs with -T (no TTY allocation) and under a timeout.
- Signal handlers terminate the child on interruption.
- The script propagates the child's exit status.

**Status:** Applied
