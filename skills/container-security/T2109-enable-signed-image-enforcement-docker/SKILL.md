---
name: t2109-enable-signed-image-enforcement-docker
description: Enable signed image enforcement (Docker)
---

# T2109: Enable signed image enforcement (Docker)

**Category:** IN
**SD Elements:** [T2109](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2109/)
**Priority:** 9

### Task T2109: Enable signed image enforcement (Docker) (DOCUMENTATION ONLY)

**Guidance:** The Universal Control Plane includes the ability to enforce running of only images that have been signed by members of a particular group. Enable this capability to prevent unsigned images from being deployed to your cluster.

Combined with the Docker Content Trust recommendations, signed image enforcement in UCP gives you more control over the validity and origination of your Docker images prior to deployment. Signed image enforcement can prohibit images that are unsigned, have malformed signatures, and/or compromised signatures from being deployed.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
