---
name: t116-test-for-regular-expression-denial-of-service
description: Bound the regular expressions that run against request-controlled input so a crafted Origin header cannot drive catastrophic backtracking.
---

# T116: Test for regular expression denial of service

**Category:** CODE_FIX
**SD Elements:** [T116](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T116/)
**Priority:** 7

**Finding:** The CORS origin allow-list is a regular expression evaluated against the attacker-controlled Origin header; the unanchored `.*.` prefix makes matching input-dependent and the pattern is applied to every request.

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
ALLOWED_ORIGINS = [
    "https://app.restaurant.com",
    "https://partner.deliveryservice.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # exact string comparison, no regex engine
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Success Criteria:**
- No regular expression is evaluated against the Origin header or any other request-controlled string in the middleware stack.
- Any regex that must remain is anchored with ^ and $ and contains no nested quantifier over an alternation.
- A request carrying a 10 KB Origin header returns in the same time as a normal request.

**Status:** Applied
