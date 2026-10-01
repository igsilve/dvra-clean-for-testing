---
name: t2602-log-typical-database-and-server-activities-and-related-met
description: Log database and server activity with enough metadata to support investigation.
---

### Task T2602: Log typical database and server activities and related metadata (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2602](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2602/)
**Priority:** 8

**Guidance:** The database should log connections, disconnections, DDL, privilege changes and failed authentications with timestamps and source identity, shipped to storage the database administrators cannot silently alter.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/session.py, app/migrations/
- Found: PostgreSQL runs with default logging and no log shipping; nothing in the repository configures it.
- Missing: postgresql.conf logging settings and a central log destination.
- Conclusion: Database activity logging is server configuration applied outside this repository.

**Recommended Action:** The database administration team should enable activity logging and ship the records centrally.

**Status:** Documented
