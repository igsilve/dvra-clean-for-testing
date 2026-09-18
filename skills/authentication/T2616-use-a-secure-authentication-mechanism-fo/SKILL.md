---
name: t2616-use-a-secure-authentication-mechanism-fo
description: Use a secure authentication mechanism for database connections (PostgreSQL)
---

# T2616: Use a secure authentication mechanism for database connections (PostgreSQL)

**Category:** IN
**SD Elements:** [T2616](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2616/)
**Priority:** 9

### Task T2616: Use a secure authentication mechanism for database connections (PostgreSQL) (DOCUMENTATION ONLY)

**Guidance:** To ensure a secure configuration, verify that the access rules in __pg.hba.conf__ follow these guidelines:
- Do not use the authentication methods `trust`, `password`, or `ident`.
- Prefer `scram-sha-256` to `md5` for password-based authentication, because MD5 is vulnerable to packet replay attacks. However, if you change an existing database, you must first update the `password_encryption` setting in the __PostgreSQLql.conf__ file and require all users to create new passwords.
- Do not allow remote access to the administration account unless required.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
