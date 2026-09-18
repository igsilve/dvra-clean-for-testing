---
name: t2619-ensure-that-row-level-security-is-correc
description: Ensure that row-level security is correctly configured (PostgreSQL)
---

# T2619: Ensure that row-level security is correctly configured (PostgreSQL)

**Category:** IN
**SD Elements:** [T2619](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2619/)
**Priority:** 7

### Task T2619: Ensure that row-level security is correctly configured (PostgreSQL) (DOCUMENTATION ONLY)

**Guidance:** Row-level security restricts users so they can access only a specific subset of the rows in a table. To review which tables use RLS, execute this query:

	SELECT oid, relname, relrowsecurity FROM pg_class WHERE relrowsecurity IS TRUE;

If a table should have an RLS policy but is not in this list, you will need to `ALTER` the table to apply the policy. To review the details of specific RLS policies, query the `pg_policy` system table.

Additionally, you must review user accounts to ensure that they do not grant `Bypass RLS`, which overrides RLS policy. Use `psql \du+` to check accounts for the `Bypass RLS` attribute. You can remove the `Bypass RLS` attribute with a command like this:

	ALTER ROLE <some-user> NOBYPASSRLS;

## Note
You create RLS policies using the `CREATE POLICY` command. A typical RLS policy restrics row access by matching a field against the name of the current user account. A slightly more elaborate process is to use a function that finds a piece of information related to the current user. This example limits `SELECT` operations to rows that match the current user's organization:

    CREATE POLICY emp_access_policy
    ON employees
    FOR SELECT
    USING (org_id =
    current_setting('app.current_user_org_id')::int);

More details about configuring RLS policies is in the official PostgreSQL documentation at https://www.PostgreSQLql.org/docs/current/ddl-rowsecurity.html

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
