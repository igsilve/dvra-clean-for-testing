---
name: t4433-prevent-path-environment-attacks-bash-shell
description: Set an explicit PATH and invoke external commands by absolute path.
---

# T4433: Prevent path environment attacks (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4433](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4433/)
**Priority:** 7

**Finding:** Commands are invoked by bare name, so resolution depends on the inherited PATH.

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
export PATH=/usr/local/bin:/usr/bin:/bin
readonly PATH

/usr/bin/mkdir -m 0750 -p postgres_data
/usr/local/bin/docker compose up "$@"
```

**Success Criteria:**
- PATH is assigned explicitly and marked readonly before any command runs.
- External binaries are invoked by absolute path.

**Status:** Applied
