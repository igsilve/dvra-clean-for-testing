---
name: implement-query-level-access-control
description: Use when Python code executes database queries without enforcing object-level authorization for tables, rows, columns, or procedures before execution.
---
# Implement query-level access control

## What This Skill Does
This skill fixes missing object-level database authorization in Python code by adding a single authorization path for database access, enforcing deny-by-default, and checking the principal, operation, and target resource before SQL runs. Use it when code calls database query APIs directly and relies only on broad roles, shared connections, or caller-provided SQL without table, column, row-scope, or procedure checks.

## Decision Table
| Situation | Action |
|-----------|--------|
| Python code calls `cursor.execute(...)`, `executemany(...)`, or similar DB APIs without checking principal/resource/operation first | Add a central guard such as `require_query_permission(...)` and route execution through a wrapper like `run_query(...)` |
| Code uses `sqlite3` and every role gets the same connection or broad access | Keep the connection library if needed, but enforce query-level checks in application code before every query |
| A query reads or writes sensitive tables, columns, row scopes, or procedure names dynamically | Validate the target object explicitly and build the allowed table/column/procedure list from policy, not from user input |
| Principal, resource, or operation is unknown or not mapped in policy | Deny by default and raise a permission error before executing SQL |
| Code already checks table, operation, columns, and row scope through a central wrapper | No action needed |

## Boundaries

### Can Do
- Add a central authorization wrapper for Python database execution paths
- Enforce deny-by-default for unmapped principal-resource-operation requests
- Restrict table, column, row-scope, and procedure access using explicit policy checks

### Cannot Do
- Infer the correct business authorization policy without project-specific rules
- Prevent access from database clients that bypass the application entirely
- Replace parameterized SQL protections; this is authorization, not SQL injection mitigation

## Gotchas
- Checking only the role once at request entry: this is wrong because later query paths can still access unauthorized tables or columns
- Building `SELECT` columns from user input: this is wrong because dynamic column lists must come only from an approved policy
- Guarding reads but not updates/deletes/procedure calls: this is wrong because write and execute paths need the same resource-level checks

## Quick Verification
```bash
# Confirm a central authorization guard/wrapper exists
rg -n "def (require_query_permission|is_query_allowed|run_query|require_column_permissions|require_row_scope_permission)\b" .

# Find unguarded dangerous Python DB API calls that may bypass the wrapper
rg -n "(cursor\.execute|cursor\.executemany|cursor\.executescript|connection\.execute|connection\.executemany|connection\.executescript)\s*\(" .

# Build check for Python files across app/library/CLI/service layouts
python -m py_compile $(rg --files -g '*.py')

# Run project tests if present
python -m pytest -q
```