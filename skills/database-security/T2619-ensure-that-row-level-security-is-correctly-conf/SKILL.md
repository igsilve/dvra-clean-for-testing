---
name: t2619-ensure-that-row-level-security-is-correctly-configured-pos
description: Configure row-level security policies on the tables holding user data.
---

### Task T2619: Ensure that row-level security is correctly configured (PostgreSQL) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2619](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2619/)
**Priority:** 7

**Guidance:** Row-level security should be enabled on the user-scoped tables with policies that restrict each application role to the rows it owns, so a flaw in application code cannot expose another user's records.

**Why Not Code-Fixable:**
- Searched: app/db/models.py, app/migrations/versions/
- Found: The migrations create tables with no row-level security, and the application connects as a single privileged role that any policy would bypass.
- Missing: Database roles for the application's identities and the migration that would enable and define the policies.
- Conclusion: Row-level security requires a database role model that the deployment does not have; it is a database design change owned by the database administrators.

**Recommended Action:** The database administration team should define the role model and row-level security policies.

**Status:** Documented
