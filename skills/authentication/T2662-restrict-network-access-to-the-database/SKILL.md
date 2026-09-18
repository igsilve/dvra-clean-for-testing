---
name: t2662-restrict-network-access-to-the-database
description: Restrict network access to the database server
---

# T2662: Restrict network access to the database server

**Category:** IN
**SD Elements:** [T2662](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2662/)
**Priority:** 10

### Task T2662: Restrict network access to the database server (DOCUMENTATION ONLY)

**Guidance:** To reduce the attack surface of your system, limit network access to the database server. Potential measures include:
- Configuring firewall rules to allow traffic only for authorized IP addresses and ports
- Using network segmentation to place the database server in a more secure environment
- Applying product-specific features in your database that limit network connectivity
- Using features like Private Link to isolate database services in a cloud environment

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
