---
name: t305-verify-that-your-application-dynamically-loads-code-only-fr
description: Resolve loadable locations from a fixed absolute base rather than the process working directory.
---

# T305: Verify that your application dynamically loads code only from secure locations

**Category:** CODE_FIX
**SD Elements:** [T305](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T305/)
**Priority:** 8

**Finding:** The static mount resolves "static" relative to the process working directory rather than an absolute, trusted location.

**Code to Fix:**
```python
# app/main.py lines 11-13
def setup_static_files_and_docs(app: FastAPI):
    """Setup static files and custom documentation endpoints with favicon"""
    app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Required Fix:**
```python
# app/main.py
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


def setup_static_files_and_docs(app: FastAPI):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

**Success Criteria:**
- Every filesystem location the application loads from is an absolute path derived from the module location.
- Starting the process from a different working directory does not change which files are served.

**Status:** Applied
