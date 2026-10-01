---
name: t1237-test-that-the-docker-daemon-and-its-files-are-audited-dock
description: Verify that the Docker daemon and its files are being audited.
---

### Task T1237: Test that the Docker daemon and its files are audited (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1237](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1237/)
**Priority:** 8

**Guidance:** Verification means confirming the audit rules are loaded, touching an audited path and observing the resulting record arrive in central log storage.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: No audit rules are defined in the repository.
- Missing: Access to the host audit configuration and the log pipeline.
- Conclusion: The verification is performed against host instrumentation.

**Recommended Action:** The platform team should verify audit coverage on each container host.

**Status:** Documented
