---
name: t4601-prioritize-static-network-configuration
description: Prefer static, declared network configuration over dynamically discovered addressing.
---

### Task T4601: Prioritize static network configuration (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T4601](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4601/)
**Priority:** 8

**Guidance:** Addresses, subnets and routes for the service tier should be declared and version-controlled, so connectivity does not depend on runtime discovery that an attacker could influence.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/config.py
- Found: Container addressing is left entirely to Docker's default bridge with no declared subnet, and the application resolves the database by the service name `db`.
- Missing: A declared network topology at the platform level, including subnets and address assignment.
- Conclusion: Network addressing policy is defined by the platform that hosts the containers rather than by this repository.

**Recommended Action:** The platform team should declare the network topology and addressing for the service tier.

**Status:** Documented
