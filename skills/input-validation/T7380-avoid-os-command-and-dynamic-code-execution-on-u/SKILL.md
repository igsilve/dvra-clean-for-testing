---
name: t7380-avoid-os-command-and-dynamic-code-execution-on-user-input
description: Eliminate shell invocation and dynamic evaluation of request-derived data.
---

# T7380: Avoid OS command and dynamic code execution on user input (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7380](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7380/)
**Priority:** 10

**Finding:** A shell is spawned with a command string built from request input.

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
def get_disk_usage(mount_point: MountPoint) -> str:
    result = subprocess.run(
        ["df", "-h", mount_point.value],
        capture_output=True, check=True, timeout=5,
    )
    return result.stdout.decode().strip()
```

**Success Criteria:**
- `shell=True`, `eval`, `exec` and `os.system` appear nowhere.
- Subprocess arguments are a list built from validated enum values.
- The subprocess runs under a timeout.

**Status:** Applied
