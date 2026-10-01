---
name: t7361-configure-cors-with-explicit-origins-and-never-wildcard-wi
description: Configure CORS with a concrete origin list and never combine credentialed requests with wildcard values.
---

# T7361: Configure CORS with explicit origins and never wildcard with credentials (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7361](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7361/)
**Priority:** 8

**Finding:** allow_credentials=True is combined with a wildcard-ish origin regex and wildcard methods and headers.

**Code to Fix:**
```python
# app/init_app.py lines 20-26
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*.(restaurant.com|deliveryservice.com)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

**Required Fix:**
```python
# app/init_app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.restaurant.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Success Criteria:**
- `allow_credentials=True` never appears alongside `allow_origins=["*"]` or an origin regex.
- Origins are supplied by configuration and differ between environments.

**Status:** Applied
