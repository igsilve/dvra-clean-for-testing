---
name: t1236-audit-the-docker-daemon-and-its-files-docker
description: Audit the Docker daemon and its supporting files.
---

### Task T1236: Audit the Docker daemon and its files (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1236](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1236/)
**Priority:** 8

**Guidance:** Host audit rules should record access to and modification of the daemon binary, socket, configuration and container storage directories, with the resulting records shipped to central log storage.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: No audit configuration exists in the repository.
- Missing: Host audit daemon rules and a log destination.
- Conclusion: Auditing the container runtime is host instrumentation applied outside this repository.

**Recommended Action:** The platform team should add audit rules for the daemon and its files.

**Status:** Documented
