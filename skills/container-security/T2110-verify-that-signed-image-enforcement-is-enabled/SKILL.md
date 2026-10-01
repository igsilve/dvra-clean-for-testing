---
name: t2110-verify-that-signed-image-enforcement-is-enabled-docker
description: Verify that signed image enforcement is actually in effect.
---

### Task T2110: Verify that signed image enforcement is enabled (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2110](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2110/)
**Priority:** 9

**Guidance:** Verification means attempting to run an unsigned image and confirming the platform refuses it, then confirming a signed image runs.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: No enforcement mechanism is configured, so the negative test would pass trivially.
- Missing: The enforcement layer that would be the subject of the test.
- Conclusion: The verification depends on platform enforcement that does not yet exist.

**Recommended Action:** The container platform team should perform this verification after enabling content trust.

**Status:** Documented
