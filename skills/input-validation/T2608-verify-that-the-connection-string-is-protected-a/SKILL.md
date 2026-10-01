---
name: t2608-verify-that-the-connection-string-is-protected-against-con
description: Prove with a test that hostile characters in the credential components cannot redirect the connection.
---

# T2608: Verify that the connection string is protected against connection string parameter pollution

**Category:** CODE_FIX
**SD Elements:** [T2608](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2608/)
**Priority:** 9

**Finding:** There is no encoding or validation of the interpolated credentials and host components to verify against.

**Code to Fix:**
```python
# app/config.py lines 49-53
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
```

**Required Fix:**
```python
# app/tests/security/test_connection_string.py
@pytest.mark.security
def test_password_special_characters_do_not_alter_target(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss/word?host=evil")
    url = make_url(str(Settings().DATABASE_URL))
    assert url.host == "localhost"
    assert url.database == "restaurant"
    assert url.query.get("host") is None
```

**Success Criteria:**
- A test injects delimiter characters into each component and asserts the parsed target is unchanged.
- The test fails if string interpolation is reintroduced.

**Status:** Applied
