---
name: t2105-enforce-the-use-of-client-certificate-bundles-for-unprivil
description: Require client certificate bundles for unprivileged users accessing the container orchestration control plane.
---

### Task T2105: Enforce the use of client certificate bundles for unprivileged users to access UCP (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2105](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2105/)
**Priority:** 7

**Guidance:** Access to the orchestration control plane should be authenticated with per-user client certificate bundles that carry the user's role, with short validity periods and revocation, so control-plane access is never granted by a shared credential.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, Dockerfile, start_app.sh, stop_app.sh
- Found: The deployment is a local Docker Compose stack; there is no UCP or equivalent orchestration control plane in the repository.
- Missing: An orchestration control plane, its user directory and a certificate authority issuing the bundles.
- Conclusion: There is no control plane in this deployment to configure; the control belongs to the container platform that would host the service.

**Recommended Action:** The container platform team should enforce client certificate bundles on the orchestration control plane.

**Status:** Documented
