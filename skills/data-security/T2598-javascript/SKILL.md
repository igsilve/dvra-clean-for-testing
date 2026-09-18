---
name: implement-query-level-access-control
description: Use when JavaScript code executes database queries or stored procedures without checking the current subject, action, and exact resource against an explicit allow policy.
---

# Implement query-level access control

## What This Skill Does
This skill adds query-level authorization to JavaScript database code so every database operation checks who is acting, what action is requested, and which exact table, column, procedure, or sensitive record is being targeted before the query runs. It replaces implicit trust in caller-provided roles or authenticated state with explicit subject normalization, exact resource allowlists, per-action permission checks, and fail-closed denial for unknown or unlisted access.

## Decision Table
| Situation | Action |
|-----------|--------|
| Database code calls `prepare()`, `query()`, `execute()`, `run()`, `all()`, or `get()` without an authorization check tied to subject + action + resource | Apply this fix |
| Code trusts `req.query.role`, `req.body.role`, CLI input, or other caller-controlled identity data to decide database access | Replace with normalized subject lookup from a fixed authorization map |
| Code builds dynamic column lists, table names, or stored procedure targets | Gate the exact target with the same authorization function before query construction |
| Code uses broad access rules such as authenticated-only access or role checks with no resource/action granularity | Replace with explicit per-action, per-resource allow rules |
| Code already checks normalized subject, exact action, and canonical resource before every database operation | No action needed |

## Boundaries

### Can Do
- Add centralized authorization helpers such as `normalizeSubjectId`, `getAuthorizedSubject`, `permissionKey`, and `authorizeOrThrow`
- Enforce separate `read`, `update`, `delete`, `write`, and `execute` permissions on exact tables, columns, and procedure names
- Convert caller-controlled role checks into explicit allowlists that fail closed for unknown subjects, actions, and resources

### Cannot Do
- Infer the correct business authorization model if the application has no defined subject-to-resource policy
- Guarantee row-level security for every query unless the target record or predicate is explicitly modeled in the authorization check
- Replace database parameterization or fix SQL injection; this skill is about authorization, not query sanitization

## Gotchas
- Trusting request-provided roles or subject IDs: this is wrong because callers can forge them unless the code resolves a normalized subject from a trusted source
- Checking only the action and not the exact resource: this is wrong because `read` on one column or table does not imply `read` on sensitive columns like `salary` or `ssn`
- Filtering returned columns after running a broad query: this is wrong because the unauthorized database access already happened before the application trimmed the response

## Quick Verification
```bash
# Confirm a central authorization guard exists
rg -n "authorizeOrThrow|isAuthorized|getAuthorizedSubject|permissionKey|normalizeSubjectId" .

# Find likely unguarded JavaScript database calls that may bypass the fix
rg -n "(\.prepare\(|\.query\(|\.execute\(|\.run\(|\.all\(|\.get\(|CALL\s+[A-Za-z_][A-Za-z0-9_]*)" . \
  -g '!node_modules' -g '!dist' -g '!build'

# Build + test using the JavaScript project's available toolchain
npm test
npm run build
```