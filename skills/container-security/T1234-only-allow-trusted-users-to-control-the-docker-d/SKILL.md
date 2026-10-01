---
name: t1234-only-allow-trusted-users-to-control-the-docker-daemon-dock
description: Limit control of the Docker daemon to trusted users.
---

### Task T1234: Only allow trusted users to control the Docker daemon (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1234](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1234/)
**Priority:** 8

**Guidance:** Membership of the docker group, or equivalent socket access, is equivalent to root on the host and should be restricted to a small, reviewed set of operators with access granted through a directory group rather than a local edit.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, start_app.sh, stop_app.sh, Dockerfile
- Found: The scripts assume the invoking user already has daemon access; the repository does not control who has it.
- Missing: Host user and group membership, which is managed outside the repository.
- Conclusion: Daemon access control is host account management, not application configuration.

**Recommended Action:** The platform team should review and restrict docker group membership on each host.

**Status:** Documented
