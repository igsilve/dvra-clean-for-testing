---
name: t573-prevent-uddi-ebxml-spoofing
description: Prevent spoofing of service registry entries used for service discovery.
---

### Task T573: Prevent UDDI/ebXML spoofing (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T573](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T573/)
**Priority:** 8

**Guidance:** Where a service registry is used, its entries should be authenticated and integrity-protected, and consumers should validate the identity of a discovered endpoint before contacting it.

**Why Not Code-Fixable:**
- Searched: app/apis/, app/config.py, pyproject.toml, docker-compose.yml
- Found: The service exposes a REST API and discovers nothing through a registry; there is no UDDI, ebXML or equivalent directory in the stack.
- Missing: A service registry, which this architecture does not use.
- Conclusion: The countermeasure targets a service discovery mechanism that is not part of this application.

**Recommended Action:** The architecture owners should confirm the registry remains out of scope, and revisit if service discovery is introduced.

**Status:** Documented
