---
name: t1173-verify-that-daemon-configuration-files-are-secured-docker
description: Verify that the Docker daemon configuration files are correctly secured.
---

### Task T1173: Verify that daemon configuration files are secured (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1173](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1173/)
**Priority:** 8

**Guidance:** Verification means checking ownership and mode on the daemon configuration, socket, service unit and certificate files against the expected baseline.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: The files in question are not part of the repository.
- Missing: Host filesystem access to inspect the daemon files.
- Conclusion: The verification is performed on the host, not against repository content.

**Recommended Action:** The platform team should perform the file permission audit on each container host.

**Status:** Documented
