---
name: t7379-serve-static-files-only-from-a-dedicated-non-sensitive-dir
description: Mount static files from an absolute, dedicated directory that holds nothing but public assets.
---

# T7379: Serve static files only from a dedicated non-sensitive directory (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7379](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7379/)
**Priority:** 10

**Finding:** StaticFiles is mounted on a relative "static" directory resolved from the process working directory rather than an explicit, dedicated path.

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

STATIC_DIR = Path(__file__).resolve().parent / "static"


def setup_static_files_and_docs(app: FastAPI):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

**Success Criteria:**
- The static directory is resolved from the module location, not the process working directory.
- The directory contains only assets intended to be public.
- A request for `/static/../config.py` returns 404.

**Status:** Applied
