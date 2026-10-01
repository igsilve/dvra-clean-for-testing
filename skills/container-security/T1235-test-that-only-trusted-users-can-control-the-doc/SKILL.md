---
name: t1235-test-that-only-trusted-users-can-control-the-docker-daemon
description: Verify that only trusted users can control the Docker daemon.
---

### Task T1235: Test that only trusted users can control the Docker daemon (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1235](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1235/)
**Priority:** 8

**Guidance:** Verification means enumerating the members of the docker group and the owners of the daemon socket, and confirming each is an approved operator.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, start_app.sh, stop_app.sh
- Found: Group membership is not represented in the repository.
- Missing: Host account data needed for the enumeration.
- Conclusion: The verification is a host account review.

**Recommended Action:** The platform team should enumerate and attest daemon access on each host.

**Status:** Documented
