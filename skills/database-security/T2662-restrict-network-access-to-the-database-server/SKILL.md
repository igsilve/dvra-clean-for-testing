---
name: t2662-restrict-network-access-to-the-database-server
description: Restrict network reachability of the database server.
---

### Task T2662: Restrict network access to the database server (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2662](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2662/)
**Priority:** 10

**Guidance:** The database should be reachable only from the application tier, on an internal network segment, never published to a host interface or the internet.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml
- Found: The database uses `expose` rather than a published port, which is sound, but it shares the default network with every other container and no internal-only network is declared.
- Missing: Network segmentation policy at the platform level beyond what Compose expresses.
- Conclusion: Meaningful network restriction is enforced by the platform's network policy; the compose-level change is tracked separately under the container network isolation countermeasure.

**Recommended Action:** The platform team should place the database on an internal segment with explicit ingress rules.

**Status:** Documented
