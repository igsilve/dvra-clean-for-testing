---
name: t4449-test-prevention-of-file-upload-vulnerabilities-bash-shell
description: Validate any file the script copies into the container for type and size before it is used.
---

# T4449: Test prevention of file upload vulnerabilities (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4449](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4449/)
**Priority:** 8

**Finding:** The script copies no uploaded content but also applies no validation to the files it hands to the container.

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

validate_input() {
    local path="$1" max_bytes="${2:-1048576}"
    [ -f "$path" ] || { echo "$path is not a regular file" >&2; return 1; }
    [ -L "$path" ] && { echo "$path is a symlink" >&2; return 1; }
    local size; size="$(stat -f '%z' "$path")"
    [ "$size" -le "$max_bytes" ] || { echo "$path exceeds $max_bytes bytes" >&2; return 1; }
}
```

**Success Criteria:**
- Files are checked for regular-file type, symlink status and size before use.
- Validation failure aborts the script.

**Status:** Applied
