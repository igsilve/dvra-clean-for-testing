---
name: t2597-implement-rbac-instead-of-individual-accounts
description: Grant access through roles rather than through individually managed accounts.
---

### Task T2597: Implement RBAC instead of individual accounts (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2597](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2597/)
**Priority:** 10

**Guidance:** Permissions should attach to a small set of roles that reflect job functions, with users receiving access solely by role membership, so entitlements can be reviewed and revoked as a set.

**Why Not Code-Fixable:**
- Searched: app/db/models.py, app/apis/auth/utils/roles_based_auth_checker.py, docker-compose.yml
- Found: The application itself already models three roles; the gap is at the infrastructure layer, where database and host access use shared individual accounts such as the `admin` PostgreSQL user.
- Missing: Role definitions in the database and host platforms, and a directory to attach them to.
- Conclusion: Infrastructure-level role-based access control is configured in the database server and host platform, not in this repository's source.

**Recommended Action:** The platform and database administration teams should define infrastructure roles and retire shared individual accounts.

**Status:** Documented
