---
name: t2106-verify-that-the-use-of-client-certificate-bundles-for-unpr
description: Verify that client certificate bundles are actually required for unprivileged control-plane access.
---

### Task T2106: Verify that the use of client certificate bundles for unprivileged users is enforced (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2106](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2106/)
**Priority:** 7

**Guidance:** Verification means attempting control-plane access without a bundle and confirming it is refused, and confirming that issued bundles carry the correct role and expiry.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, Dockerfile, start_app.sh, stop_app.sh
- Found: No orchestration control plane is present in this deployment.
- Missing: The control plane and its access logs against which the verification would be performed.
- Conclusion: The verification cannot be performed without the platform it targets.

**Recommended Action:** The container platform team should perform this verification on the orchestration control plane.

**Status:** Documented
