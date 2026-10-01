---
name: t4437-prevent-input-file-attacks-bash-shell
description: Validate the files the script consumes before handing them to a container.
---

# T4437: Prevent input file attacks (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4437](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4437/)
**Priority:** 8

**Finding:** The script executes a relative-path script and a file inside the container without validating either.

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

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
GAME=/app/game.py

[ -x "$SCRIPT_DIR/start_app.sh" ] || { echo "start_app.sh missing or not executable" >&2; exit 1; }

"$SCRIPT_DIR/start_app.sh" -d
docker compose exec -T web test -f "$GAME" || { echo "$GAME not found in image" >&2; exit 1; }
docker compose exec -T web python3 "$GAME"
```

**Success Criteria:**
- Every file the script executes is checked for existence and type first.
- Paths are absolute and not influenced by the caller's working directory.

**Status:** Applied
