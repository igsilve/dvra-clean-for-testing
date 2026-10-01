---
name: t2615-limit-network-access-by-blocking-connections-from-unknown
description: Restrict which network sources may connect to PostgreSQL.
---

### Task T2615: Limit network access by blocking connections from unknown IP addresses (PostgreSQL) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2615](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2615/)
**Priority:** 8

**Guidance:** Host-based access rules should permit connections only from the application's address range, with everything else rejected, reinforced by network-level filtering.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/session.py
- Found: The database is reachable from any container on the shared default network; access rules live in pg_hba.conf, which is not in the repository.
- Missing: pg_hba.conf and the network policy configuration.
- Conclusion: Source restriction is database server and network configuration applied outside this repository.

**Recommended Action:** The database administration team should tighten pg_hba.conf and the surrounding network rules.

**Status:** Documented
