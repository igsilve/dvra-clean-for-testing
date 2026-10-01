---
name: t2652-consider-adding-plugins-for-stronger-authentication-protoc
description: Strengthen database authentication with plugins for stronger protocols and password complexity.
---

### Task T2652: Consider adding plugins for stronger authentication protocols and stricter password complexity rules (MariaDB) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2652](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2652/)
**Priority:** 9

**Guidance:** The database should enforce password complexity, expiry and reuse restrictions through its authentication plugins, or delegate authentication to a central directory.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/config.py
- Found: The database uses a static password supplied through the compose environment; no complexity or expiry policy is applied.
- Missing: Server-side authentication plugin configuration.
- Conclusion: Authentication plugins are installed and configured on the database server.

**Recommended Action:** The database administration team should enable password policy enforcement on the server.

**Status:** Documented
