---
name: t1157-verify-that-the-aufs-storage-driver-is-not-used-docker
description: Verify that the aufs storage driver is not in use on hosts running these containers.
---

### Task T1157: Verify that the aufs storage driver is not used (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1157](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1157/)
**Priority:** 8

**Guidance:** Verification means inspecting the Docker daemon's active storage driver and confirming it is overlay2 or another supported driver rather than aufs.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: The storage driver is a daemon-level setting; nothing in the repository selects or references it.
- Missing: Access to the host's Docker daemon configuration and `docker info` output.
- Conclusion: Storage driver selection is host daemon configuration that no repository change can influence.

**Recommended Action:** The platform team should confirm the storage driver on each container host.

**Status:** Documented
