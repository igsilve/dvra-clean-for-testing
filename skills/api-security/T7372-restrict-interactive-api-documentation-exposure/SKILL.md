---
name: t7372-restrict-interactive-api-documentation-exposure-in-product
description: Serve the interactive API documentation only outside production.
---

# T7372: Restrict interactive API documentation exposure in production (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7372](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7372/)
**Priority:** 7

**Finding:** Swagger UI is re-registered at /docs unconditionally, with no environment guard, after being disabled in the FastAPI constructor.

**Code to Fix:**
```python
# app/main.py lines 23-29
    @app.get("/docs", include_in_schema=False)
    def overridden_swagger():
        return get_swagger_ui_html(
            openapi_url=f"{app.root_path}/openapi.json",
            title=settings.TITLE,
            swagger_favicon_url=f"{app.root_path}/static/img/favicon-32x32.png",
        )
```

**Required Fix:**
```python
# app/main.py
def setup_static_files_and_docs(app: FastAPI):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    if settings.ENVIRONMENT is ENV.PRODUCTION:
        return

    @app.get("/docs", include_in_schema=False)
    def overridden_swagger():
        ...
```

**Success Criteria:**
- GET /docs, /redoc, / and /openapi.json all return 404 when ENV=production.
- The documentation routes are still available in development and testing.

**Status:** Applied
