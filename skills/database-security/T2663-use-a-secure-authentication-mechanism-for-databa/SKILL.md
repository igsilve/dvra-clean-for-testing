---
name: t2663-use-a-secure-authentication-mechanism-for-database-connect
description: Use a secure authentication mechanism for database connections generally.
---

### Task T2663: Use a secure authentication mechanism for database connections (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2663](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2663/)
**Priority:** 9

**Guidance:** Connections should authenticate with scram-sha-256, client certificates or short-lived credentials issued by a secret store, rather than a static password shared between environments.

**Why Not Code-Fixable:**
- Searched: app/config.py, app/db/session.py, docker-compose.yml
- Found: A static password is passed through the environment and used for every connection.
- Missing: A secret store capable of issuing short-lived database credentials, and server support for the chosen method.
- Conclusion: Moving to certificate or dynamically issued credentials requires infrastructure the deployment does not yet have.

**Recommended Action:** The database administration and platform teams should select and roll out the stronger mechanism.

**Status:** Documented
