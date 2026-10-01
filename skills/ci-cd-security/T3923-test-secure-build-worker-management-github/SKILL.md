---
name: t3923-test-secure-build-worker-management-github
description: Verify that build workers are isolated, ephemeral and least-privileged.
---

### Task T3923: Test secure build worker management (GitHub) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T3923](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3923/)
**Priority:** 8

**Guidance:** Verification means confirming workers are destroyed after each job, do not share state, hold no standing production credentials, and are provisioned from a controlled image.

**Why Not Code-Fixable:**
- Searched: Repository root, .github/ (absent)
- Found: No build worker fleet is associated with this repository.
- Missing: The worker fleet and its configuration.
- Conclusion: The verification targets infrastructure that does not exist for this project.

**Recommended Action:** The CI/CD platform team should verify the worker baseline once build automation exists.

**Status:** Documented
