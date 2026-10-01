---
name: t349-protect-audit-information-and-logs-against-unauthorized-acc
description: Protect audit records from unauthorized access and modification.
---

### Task T349: Protect audit information and logs against unauthorized access (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T349](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T349/)
**Priority:** 7

**Guidance:** Audit records should be shipped off the generating host promptly, stored append-only with restricted read access, retained for the required period and monitored for gaps that would indicate tampering.

**Why Not Code-Fixable:**
- Searched: app/init_app.py, docker-compose.yml, Dockerfile
- Found: The application writes no audit log today and the containers have no log shipping configured, so there is no protected store to speak of.
- Missing: Central log storage with access control, retention and integrity protection.
- Conclusion: Protecting audit records requires log infrastructure outside this repository; producing the records is tracked separately under the structured audit logging countermeasure.

**Recommended Action:** The security operations team should provide access-controlled, append-only log storage for this service.

**Status:** Documented
