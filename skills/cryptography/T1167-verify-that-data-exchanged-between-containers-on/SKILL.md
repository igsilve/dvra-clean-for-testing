---
name: t1167-verify-that-data-exchanged-between-containers-on-different
description: Verify that traffic between containers on different nodes is encrypted.
---

### Task T1167: Verify that data exchanged between containers on different nodes on the overlay network is encrypted (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1167](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1167/)
**Priority:** 8

**Guidance:** Verification means confirming the overlay network is created with encryption enabled and capturing inter-node traffic to confirm it is not readable in plaintext.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, start_app.sh
- Found: The deployment is single-host Compose with no overlay network, so there is no cross-node traffic in this configuration.
- Missing: A multi-node cluster and its overlay network configuration.
- Conclusion: The verification applies to a clustered deployment that this repository does not define.

**Recommended Action:** The container platform team should verify overlay encryption if the service is deployed across nodes.

**Status:** Documented
