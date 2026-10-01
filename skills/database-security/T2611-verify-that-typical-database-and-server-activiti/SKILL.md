---
name: t2611-verify-that-typical-database-and-server-activities-along-w
description: Verify that database and server activity is being logged with the required metadata.
---

### Task T2611: Verify that typical database and server activities, along with related metadata, are logged (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2611](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2611/)
**Priority:** 8

**Guidance:** Verification means confirming the logging settings are active, generating a representative event and observing it arrive in central storage with the expected fields.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/session.py
- Found: No logging configuration or destination exists to verify.
- Missing: The database logging configuration and central log storage.
- Conclusion: The verification depends on server configuration outside this repository.

**Recommended Action:** The database administration team should verify logging once it is configured.

**Status:** Documented
