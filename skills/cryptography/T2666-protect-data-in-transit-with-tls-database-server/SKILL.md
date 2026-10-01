---
name: t2666-protect-data-in-transit-with-tls-database-server
description: Require TLS for all connections to the database server.
---

### Task T2666: Protect data in transit with TLS (Database Server) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2666](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2666/)
**Priority:** 8

**Guidance:** The database server should refuse plaintext connections outright, presenting a certificate issued by a known CA, so that no client can negotiate an unencrypted session.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/session.py
- Found: The stock PostgreSQL image accepts plaintext connections and nothing in the deployment forbids them.
- Missing: Server-side pg_hba.conf entries and certificate material.
- Conclusion: Refusing plaintext is enforced by the database server configuration, outside this repository.

**Recommended Action:** The database administration team should require hostssl entries and remove plaintext host entries.

**Status:** Documented
