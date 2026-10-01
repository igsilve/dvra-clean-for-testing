---
name: t2620-protect-data-in-transit-with-tls-postgresql
description: Require TLS for client connections to PostgreSQL.
---

### Task T2620: Protect data in transit with TLS (PostgreSQL) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2620](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2620/)
**Priority:** 9

**Guidance:** The server should be configured with a certificate and require SSL for all client connections, with clients verifying the server certificate against a known CA.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/session.py, app/config.py
- Found: PostgreSQL runs with stock settings and the application connects with a URL carrying no sslmode; the server-side requirement is set in postgresql.conf and pg_hba.conf.
- Missing: Server configuration files and certificate material, neither of which is in the repository.
- Conclusion: Requiring TLS is a database server configuration change; the matching client-side change is tracked separately under the data-in-transit countermeasure.

**Recommended Action:** The database administration team should issue a server certificate and require SSL in pg_hba.conf.

**Status:** Documented
