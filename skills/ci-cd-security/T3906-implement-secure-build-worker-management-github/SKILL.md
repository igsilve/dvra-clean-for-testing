---
name: t3906-implement-secure-build-worker-management-github
description: Manage build workers securely.
---

### Task T3906: Implement secure build worker management (GitHub) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T3906](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3906/)
**Priority:** 8

**Guidance:** Build workers should be ephemeral, isolated per job, run with least privilege, have no standing access to production credentials, and be rebuilt from a known-good image rather than reused across jobs.

**Why Not Code-Fixable:**
- Searched: Repository root, .github/ (absent), Dockerfile, docker-compose.yml
- Found: No build automation is configured; images are built locally through Docker Compose.
- Missing: A build worker fleet and its provisioning configuration.
- Conclusion: Build worker management is an infrastructure concern owned by the CI/CD platform, with nothing in this repository to change.

**Recommended Action:** The CI/CD platform team should define and own the build worker baseline.

**Status:** Documented
