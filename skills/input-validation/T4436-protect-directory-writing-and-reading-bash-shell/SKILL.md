---
name: t4436-protect-directory-writing-and-reading-bash-shell
description: Create directories with an explicit restrictive mode and verify ownership before writing.
---

# T4436: Protect directory writing and reading (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4436](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4436/)
**Priority:** 8

**Finding:** mkdir -p creates postgres_data relative to the caller's working directory with default permissions.

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
umask 077

DATA_DIR="$(pwd -P)/postgres_data"
mkdir -m 0700 -p "$DATA_DIR"

if [ "$(stat -f '%u' "$DATA_DIR")" != "$(id -u)" ]; then
    echo "postgres_data is not owned by the current user" >&2
    exit 1
fi
```

**Success Criteria:**
- Directories are created with an explicit mode, not the inherited umask default.
- Ownership is verified before the directory is used.
- The path is resolved absolutely.

**Status:** Applied
