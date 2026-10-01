---
name: t318-verify-security-of-cross-origin-resource-sharing-cors
description: Replace the permissive CORS configuration with an explicit origin allow-list and a narrow method and header set.
---

# T318: Verify security of cross origin resource sharing (CORS)

**Category:** CODE_FIX
**SD Elements:** [T318](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T318/)
**Priority:** 8

**Finding:** CORS is configured with a permissive unanchored origin regex together with allow_credentials=True and wildcard methods and headers.

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
    allow_origins=settings.ALLOWED_ORIGINS,   # explicit list, loaded from config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)
```

**Success Criteria:**
- `allow_origin_regex` is no longer used.
- `allow_methods` and `allow_headers` list explicit values, never `*`, while credentials are allowed.
- A preflight from `https://evil-restaurant.com.attacker.net` receives no Access-Control-Allow-Origin header.

**Status:** Applied
