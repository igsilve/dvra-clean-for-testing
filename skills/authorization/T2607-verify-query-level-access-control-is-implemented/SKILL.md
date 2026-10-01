---
name: t2607-verify-query-level-access-control-is-implemented
description: Verify that access control is enforced at the query level in the database.
---

### Task T2607: Verify query-level access control is implemented (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2607](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2607/)
**Priority:** 8

**Guidance:** Verification means confirming the database enforces per-row or per-view restrictions independently of the application, by connecting as a restricted role and observing that it cannot read rows outside its scope.

**Why Not Code-Fixable:**
- Searched: app/db/models.py, app/db/session.py, app/migrations/versions/
- Found: All access uses one privileged database account; no row-level security policies or restricted views are defined in the migrations.
- Missing: Database roles, row-level security policies and the migration that would create them.
- Conclusion: Query-level access control is configured in the database server; there is no policy in this repository to verify.

**Recommended Action:** The database administration team should define and verify query-level access controls.

**Status:** Documented
