---
name: verify-function-level-authorization-in-api
description: Use when Python code exposes privileged API or service actions that may be reachable directly without explicit function-level authorization tied to the requested action.
---

# Verify that function level authorization is implemented in API

## What This Skill Does
This skill fixes direct-request or forced-browsing authorization flaws in Python APIs and service entry points by ensuring privileged actions perform an explicit authorization check before any protected work runs. It centralizes authorization for administrative handlers, requires privileged functions in regular controllers or services to call the same check, and enforces deny-by-default so endpoints without explicit role, group, or user rules are rejected.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Python endpoint, controller method, service function, or CLI/admin action performs privileged work without checking the caller's role, group, or username first | Apply a shared `authorization_check`/`is_authorized` guard at the start of the function and return deny on failure |
| Administrative controllers exist | Move authorization into a shared administrative base controller and make all admin controllers inherit it |
| A privileged action lives in a regular controller or service instead of an admin controller | Add an explicit call to the shared authorization function or a decorator that uses the same rules |
| Routing or dispatch selects privileged actions by path or command name but missing metadata means "allowed" | Change to deny by default and allow only when explicit per-action rules exist |
| Code already checks the specific action with explicit allow rules and denies missing metadata | No action needed |

## Boundaries

### Can Do
- Add or reuse a centralized Python authorization helper such as `authorization_check()` or `is_authorized()`
- Refactor administrative controllers to inherit a shared base authorization path
- Add explicit function-entry authorization checks or decorators to privileged actions in any Python app shape

### Cannot Do
- Infer correct business roles, groups, or allowed users without project-specific policy input
- Guarantee framework-wide middleware or router behavior if authorization is intentionally bypassed later in custom code
- Prove every endpoint is safe without code review and test coverage of all dispatch paths

## Gotchas
- Checking only authentication, not authorization: a logged-in user is not automatically allowed to run an admin action
- Putting the check after privileged work starts: partial execution can still leak data or change state before denial
- Allowing missing rules to fall through as success: function-level authorization must deny when metadata or mappings are absent

## Quick Verification
```bash
# Confirm a shared authorization guard exists somewhere in the Python codebase
rg -n --glob '*.py' 'def (authorization_check|is_authorized)\(' .

# Find likely unguarded privileged functions/endpoints that mention admin/delete/export/report actions
# but do not obviously use authorization_check/is_authorized/require_authorization nearby
rg -n --glob '*.py' 'def .*(admin|delete|export|remove|reset|grant|revoke|report)' .

# Find direct dispatch to privileged admin paths or actions
rg -n --glob '*.py' '(/admin/|admin_[a-zA-Z_]+|delete_user|export_all_users|admin_report_action)' .

# Find places where privileged functions are protected by a shared guard or decorator
rg -n --glob '*.py' '(authorization_check\(|is_authorized\(|@require_authorization)' .

# Build/test with generic Python toolchain commands that work across common project shapes
python -m compileall .
python -m pytest -q
```