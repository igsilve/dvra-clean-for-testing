---
name: t576-verify-that-uddi-ebxml-spoofing-is-prevented
description: Verify that service registry spoofing is prevented.
---

### Task T576: Verify that UDDI/ebXML spoofing is prevented (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T576](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T576/)
**Priority:** 8

**Guidance:** Verification means attempting to publish or alter a registry entry without authorization and confirming the attempt is refused, then confirming consumers reject an unverified endpoint.

**Why Not Code-Fixable:**
- Searched: app/apis/, app/config.py, docker-compose.yml
- Found: No service registry is present in the deployment.
- Missing: The registry that would be the subject of the test.
- Conclusion: The verification has no subject in this architecture.

**Recommended Action:** The architecture owners should record the countermeasure as not applicable unless service discovery is adopted.

**Status:** Documented
