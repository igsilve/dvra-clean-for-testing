---
name: t4443-prevent-cryptographic-failures-bash-shell
description: Keep key material out of the shell scripts and pass secrets to the containers through a secret store rather than the environment.
---

# T4443: Prevent cryptographic failures (Bash/Shell)

**Category:** CODE_FIX
**SD Elements:** [T4443](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4443/)
**Priority:** 8

**Finding:** The operational scripts handle no key material and provide no cryptographic controls around the secrets passed into the containers.

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

# Secrets are read by the runtime from Docker secrets, never exported here.
docker compose up "$@"
```

**Success Criteria:**
- No script exports or echoes a credential.
- `umask 077` is set before any file the script creates.
- Secrets reach the container through a secret mount, not an environment variable in a committed file.

**Status:** Applied
