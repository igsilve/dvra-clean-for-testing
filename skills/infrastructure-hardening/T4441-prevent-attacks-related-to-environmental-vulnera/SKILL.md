---
name: t4441-prevent-attacks-related-to-environmental-vulnerabilities-b
description: Control the environment the script runs in rather than inheriting whatever the caller provides.
---

# T4441: Prevent attacks related to environmental vulnerabilities (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4441](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4441/)
**Priority:** 8

**Finding:** The script runs with the caller's inherited environment and PATH and passes it straight into the container runtime.

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
IFS=$'\n\t'
export PATH=/usr/local/bin:/usr/bin:/bin
umask 077

mkdir -m 0750 -p postgres_data
/usr/bin/env -i PATH="$PATH" HOME="$HOME" docker compose up "$@"
```

**Success Criteria:**
- PATH and IFS are set explicitly at the top of the script.
- The script runs with a clean environment rather than the caller's.
- `set -euo pipefail` is present.

**Status:** Applied
