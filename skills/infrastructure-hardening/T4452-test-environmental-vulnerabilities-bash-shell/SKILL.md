---
name: t4452-test-environmental-vulnerabilities-bash-shell
description: Resolve the script and its dependencies from absolute paths so the caller's environment cannot redirect them.
---

# T4452: Test environmental vulnerabilities (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4452](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4452/)
**Priority:** 8

**Finding:** The script invokes a sibling script by relative path, resolving it from the caller's working directory and environment.

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
export PATH=/usr/local/bin:/usr/bin:/bin

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

"$SCRIPT_DIR/start_app.sh" -d
docker compose exec -T web python3 /app/game.py
```

**Success Criteria:**
- Sibling scripts are invoked through an absolute, resolved path.
- PATH is set before any external command runs.
- The script does not depend on the caller's working directory.

**Status:** Applied
