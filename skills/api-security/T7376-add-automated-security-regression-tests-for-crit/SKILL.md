---
name: t7376-add-automated-security-regression-tests-for-critical-contr
description: Add an automated regression suite that exercises the critical security controls so a future change cannot silently remove them.
---

# T7376: Add automated security regression tests for critical controls (FastAPI)

**Category:** CODE_FIX
**SD Elements:** [T7376](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T7376/)
**Priority:** 10

**Finding:** The pytest configuration defines no security regression suite or marker; the existing tests cover functional behavior only.

**Code to Fix:**
```toml
# pyproject.toml lines 42-48
[tool.pytest.ini_options]
norecursedirs = [
  ".*",
  "build",
  "dist",
  "postgres_data",
]
```

**Required Fix:**
```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = ["security: security control regression tests"]

# app/tests/security/test_controls.py
@pytest.mark.security
def test_unsigned_jwt_is_rejected(client):
    forged = jwt.encode({"sub": "chef"}, "wrong-key", algorithm="HS256")
    assert client.get("/profile", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


@pytest.mark.security
def test_debug_endpoint_is_absent(client):
    assert client.get("/debug").status_code == 404
```

**Success Criteria:**
- A `security` test package exists and runs in CI on every change.
- There is at least one failing-closed test per critical control: JWT verification, endpoint authorization, object ownership, command execution and CORS.
- Reverting any hardening change makes a security test fail.

**Status:** Applied
