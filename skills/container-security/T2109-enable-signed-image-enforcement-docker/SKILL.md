---
name: t2109-enable-signed-image-enforcement-docker
description: Require that only signed images may be pulled or run.
---

### Task T2109: Enable signed image enforcement (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2109](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2109/)
**Priority:** 9

**Guidance:** Content trust should be enforced at the daemon or admission layer so an unsigned image is refused, with signing keys held in a managed store and rotated.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: Images are referenced by floating tag with no signature requirement; enforcement is a daemon or platform setting.
- Missing: Daemon content-trust configuration or an admission controller, plus a signing key hierarchy.
- Conclusion: Signed-image enforcement is applied by the container platform, not by a file in this repository.

**Recommended Action:** The container platform team should enable and enforce content trust.

**Status:** Documented
