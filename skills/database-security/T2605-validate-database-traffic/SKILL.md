---
name: t2605-validate-database-traffic
description: Validate and monitor database traffic for anomalous statements.
---

### Task T2605: Validate database traffic (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2605](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2605/)
**Priority:** 9

**Guidance:** A database activity monitor or proxy should inspect statements for patterns such as injection attempts or bulk extraction, alerting on deviations from the application's normal query profile.

**Why Not Code-Fixable:**
- Searched: app/db/session.py, docker-compose.yml
- Found: The application connects directly to PostgreSQL with no intermediary and no statement monitoring.
- Missing: A database activity monitoring component and its alert routing.
- Conclusion: Traffic validation is delivered by a monitoring appliance or proxy deployed alongside the database.

**Recommended Action:** The database administration and security operations teams should deploy database activity monitoring.

**Status:** Documented
