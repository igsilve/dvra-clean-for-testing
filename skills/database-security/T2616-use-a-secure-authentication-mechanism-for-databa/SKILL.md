---
name: t2616-use-a-secure-authentication-mechanism-for-database-connect
description: Use a strong authentication mechanism for PostgreSQL connections.
---

### Task T2616: Use a secure authentication mechanism for database connections (PostgreSQL) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2616](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2616/)
**Priority:** 9

**Guidance:** The server should require scram-sha-256 or certificate authentication for every connection, with md5 and trust methods removed from the host-based configuration.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/config.py, app/db/session.py
- Found: The application supplies a username and password; the accepted authentication method is decided by the server's pg_hba.conf, which is not part of the repository.
- Missing: pg_hba.conf and the server's password_encryption setting.
- Conclusion: The authentication mechanism is chosen in the database server configuration.

**Recommended Action:** The database administration team should require scram-sha-256 and remove weaker methods.

**Status:** Documented
