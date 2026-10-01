---
name: t7370-return-generic-errors-and-disable-debug-output-in-producti
description: Return a generic error to the client, log the detail internally, and never let a bare except mask the real failure.
---

# T7370: Return generic errors and disable debug output in production (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7370](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7370/)
**Priority:** 7

**Finding:** A bare except swallows the real error and re-raises a generic Exception, which FastAPI surfaces as an unhandled 500 with a traceback when debug output is enabled.

**Code to Fix:**
```python
# app/apis/admin/utils.py lines 11-13
        usage = result.stdout.strip().decode()
    except:
        raise Exception("An unexpected error was observed")
```

**Required Fix:**
```python
# app/apis/admin/utils.py
import logging

logger = logging.getLogger(__name__)


def get_disk_usage(mount_point: str) -> str:
    try:
        result = subprocess.run(
            ["df", "-h", mount_point],
            capture_output=True, check=True, timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.exception("df failed for mount_point=%s", mount_point)
        raise HTTPException(status_code=500, detail="Unable to read disk statistics")

    return result.stdout.decode().strip()
```

**Success Criteria:**
- No bare `except:` remains in the codebase.
- Client-facing error messages contain no stack trace, command string or file path.
- The underlying exception is written to the application log.

**Status:** Applied
