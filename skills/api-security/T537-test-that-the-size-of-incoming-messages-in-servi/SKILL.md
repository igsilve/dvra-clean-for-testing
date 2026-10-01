---
name: t537-test-that-the-size-of-incoming-messages-in-services-is-rest
description: Provide an enforced message-size ceiling that a test can exercise and confirm.
---

# T537: Test that the size of incoming messages in services is restricted

**Category:** CODE_FIX
**SD Elements:** [T537](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T537/)
**Priority:** 8

**Finding:** There is no body-size ceiling to test against: the application accepts requests of any length.

**Code to Fix:**
```python
# app/init_app.py lines 11-19
    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        servers=settings.SERVERS,
        root_path=settings.ROOT_PATH,
        docs_url=None,
        redoc_url=None,
    )
```

**Required Fix:**
```python
# app/tests/integration/test_body_size_limit.py
def test_oversized_body_is_rejected(client):
    payload = {"description": "A" * (2 * 1024 * 1024)}
    response = client.put("/menu", json=payload)
    assert response.status_code == 413
```

**Success Criteria:**
- An automated test submits a body above the ceiling and asserts a 413 response.
- The test fails if the middleware is removed.

**Status:** Applied
