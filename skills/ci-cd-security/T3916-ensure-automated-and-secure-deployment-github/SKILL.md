---
name: t3916-ensure-automated-and-secure-deployment-github
description: Automate deployment so releases are reproducible and no person deploys by hand.
---

### Task T3916: Ensure automated and secure deployment (GitHub) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T3916](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3916/)
**Priority:** 8

**Guidance:** Deployment should run from a reviewed pipeline against an immutable artifact, with environment approvals, automatic rollback and a recorded audit trail, rather than from a developer workstation.

**Why Not Code-Fixable:**
- Searched: start_app.sh, stop_app.sh, start_game.sh, docker-compose.yml
- Found: Deployment is a shell script that runs `docker compose up` on whatever host the operator is sitting at.
- Missing: A deployment pipeline, target environment definitions and release approval gates.
- Conclusion: Automating deployment requires CI/CD infrastructure and environment definitions that sit outside this repository.

**Recommended Action:** The CI/CD owners should build the deployment pipeline and retire manual script-based deployment.

**Status:** Documented
