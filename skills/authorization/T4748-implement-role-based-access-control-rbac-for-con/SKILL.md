---
name: t4748-implement-role-based-access-control-rbac-for-container-orc
description: Implement role-based access control for the container orchestration platform.
---

### Task T4748: Implement Role-Based Access Control (RBAC) for container orchestration (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T4748](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T4748/)
**Priority:** 10

**Guidance:** Orchestration permissions should be granted through roles bound to groups, with separate roles for deploy, read and administrative operations, and no standing cluster-administrator access.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, start_app.sh, stop_app.sh
- Found: Deployment is driven by shell scripts invoking Docker Compose on the host; anyone with Docker socket access has full control.
- Missing: An orchestration platform with an authorization model, and a directory to bind roles to.
- Conclusion: There is no orchestration authorization layer in this deployment to configure.

**Recommended Action:** The container platform team should implement orchestration RBAC when the service is deployed to a managed platform.

**Status:** Documented
