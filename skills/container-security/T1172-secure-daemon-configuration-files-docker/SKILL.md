---
name: t1172-secure-daemon-configuration-files-docker
description: Secure the Docker daemon configuration files on the container hosts.
---

### Task T1172: Secure daemon configuration files (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1172](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1172/)
**Priority:** 8

**Guidance:** The daemon configuration, socket and certificate files should be owned by root, not writable by any other user, and audited for change, so nobody can alter daemon behaviour without detection.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh, stop_app.sh
- Found: No daemon configuration file is present in the repository.
- Missing: Filesystem access to the container hosts where those files live.
- Conclusion: Daemon file permissions are host hardening, not a change in application source.

**Recommended Action:** The platform team should apply ownership and permission hardening to the daemon files.

**Status:** Documented
