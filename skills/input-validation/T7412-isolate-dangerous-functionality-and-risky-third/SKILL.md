---
name: t7412-isolate-dangerous-functionality-and-risky-third-party-comp
description: Run the risky operation outside the application process with reduced privileges.
---

# T7412: Isolate dangerous functionality and risky third-party components using sandboxing or encapsulation

**Category:** CODE_FIX
**SD Elements:** [T7412](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7412/)
**Priority:** 9

**Finding:** The subprocess call runs in the application's own process context with no sandbox or privilege separation.

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
        capture_output=True,
        check=True,
        timeout=5,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},   # clean environment
        cwd="/",
    )
    return result.stdout.decode().strip()

# The container itself runs non-root with all capabilities dropped and a
# read-only root filesystem, so the subprocess inherits no privilege.
```

**Success Criteria:**
- The subprocess runs with a clean environment, a fixed working directory and a timeout.
- The container drops all capabilities and runs as a non-root user.
- Third-party components with broad reach run in their own isolation boundary.

**Status:** Applied
