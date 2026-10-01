---
name: t7377-escape-and-sanitize-user-content-in-server-rendered-html-f
description: Escape values interpolated into server-rendered HTML for the context they appear in.
---

# T7377: Escape and sanitize user content in server-rendered HTML (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7377](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7377/)
**Priority:** 8

**Finding:** Server-rendered documentation HTML interpolates configuration values without escaping.

**Code to Fix:**
```python
# app/main.py lines 15-21
    @app.get("/", include_in_schema=False)
    def root_docs():
        return get_swagger_ui_html(
            openapi_url=f"{app.root_path}/openapi.json",
            title=settings.TITLE,
            swagger_favicon_url=f"{app.root_path}/static/img/favicon-32x32.png",
        )
```

**Required Fix:**
```python
# app/main.py
from markupsafe import escape
from urllib.parse import quote

@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url=quote(f"{app.root_path}/openapi.json", safe="/:"),
        title=escape(settings.TITLE),
        swagger_favicon_url=quote(f"{app.root_path}/static/img/favicon-32x32.png", safe="/:"),
    )
```

**Success Criteria:**
- Values placed in HTML text are HTML-escaped; values placed in URLs are URL-encoded.
- No raw string concatenation produces markup.

**Status:** Applied
