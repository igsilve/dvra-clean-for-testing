---
name: t1159-verify-that-tls-authentication-is-configured-for-the-docke
description: Verify that TLS client authentication is configured for the Docker daemon.
---

### Task T1159: Verify that TLS authentication is configured for the Docker daemon (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1159](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1159/)
**Priority:** 8

**Guidance:** Verification means confirming the daemon listens only on a TLS socket with client certificate verification enabled, and that an unauthenticated connection to the daemon is refused.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, start_app.sh, stop_app.sh
- Found: The scripts talk to the daemon over the local socket; daemon TLS settings are not represented in the repository.
- Missing: Access to the daemon's configuration and its certificate material.
- Conclusion: Daemon TLS is host configuration outside this repository's control.

**Recommended Action:** The platform team should verify daemon TLS configuration on each container host.

**Status:** Documented
