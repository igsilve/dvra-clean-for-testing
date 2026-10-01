---
name: t659-test-that-user-supplied-inputs-are-validated-before-being-p
description: Remove the shell from the execution path and constrain the argument to a validated value.
---

# T659: Test that user-supplied inputs are validated before being passed to OS commands

**Category:** CODE_FIX
**SD Elements:** [T659](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T659/)
**Priority:** 10

**Finding:** The `parameters` string is concatenated onto "df -h " and executed with shell=True, giving direct command injection.

**Code to Fix:**
```python
# app/apis/admin/utils.py lines 4-10
def get_disk_usage(parameters: str):
    command = "df -h " + parameters

    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
```

**Required Fix:**
```python
# app/apis/admin/utils.py
import subprocess
from enum import Enum


class MountPoint(str, Enum):
    ROOT = "/"
    DATA = "/var/lib/postgresql/data"


def get_disk_usage(mount_point: MountPoint) -> str:
    result = subprocess.run(
        ["df", "-h", mount_point.value],
        capture_output=True, check=True, timeout=5,      # shell=False is the default
    )
    return result.stdout.decode().strip()
```

**Success Criteria:**
- `shell=True` appears nowhere in the codebase.
- The command is passed as an argument list.
- The only variable part is drawn from a closed enum, never from a free-form string.
- A request with `parameters=/; id` returns 422 and executes nothing.

**Status:** Applied
