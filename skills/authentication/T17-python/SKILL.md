---
name: do-not-only-rely-on-client-side-authorization
description: Use when Python code makes authorization decisions from client-controlled data or fails to enforce access checks on protected server-side routes, handlers, or resources.
---
# Do not only rely on client-side authorization

## What This Skill Does
This skill fixes Client-Side Enforcement of Server-Side Security (CWE-602 / P494) in Python by moving authorization decisions to the server, using only server-controlled identity and permission data, and enforcing the same check on every protected action or resource. It applies when code trusts request headers, parameters, cookies, form fields, or UI state such as `X-User-Role`, hidden fields, or client flags to decide who may access sensitive pages, APIs, files, or actions.

## Decision Table
| Situation | Action |
|-----------|--------|
| A route, handler, CLI path, or service method uses client input like headers, params, cookies, or JSON fields to decide admin/user access | Replace the decision with a server-side authorization helper that validates identity and checks roles/permissions from server-controlled data |
| Flask or similar Python web code protects access only in the UI or front-end behavior | Add a server-side guard/decorator/helper and apply it to every protected endpoint and response path |
| Code reads fields such as `X-User-Role`, `role`, `is_admin`, or `permissions` from the request and trusts them for access control | Ignore those client-supplied authorization fields for decision-making; use them only as untrusted input if needed for logging or compatibility |
| Multiple protected routes need the same rule | Centralize the rule in a reusable function or decorator such as `require_role(...)` or `check_server_side_admin(...)` |
| Authorization already uses validated server identity plus server-side role lookup on every protected path | No action needed |

## Boundaries

### Can Do
- Replace client-trusted authorization checks with server-side role or permission checks in Python code
- Add reusable authorization helpers or decorators for protected routes and handlers
- Deny access by default when identity is missing, invalid, or lacks the required permission

### Cannot Do
- Create a full authentication system or identity provider integration from scratch
- Decide business-specific role models or permission mappings without project guidance
- Guarantee every sensitive path is found if protection happens outside the visible Python codebase or in external infrastructure

## Gotchas
- Checking a client role before a server check: this is wrong because a forged header or request field can still influence access decisions
- Protecting only the page link or front-end button: this is wrong because attackers can directly request the underlying URL or action
- Verifying identity but not re-checking authorization on each protected route: this is wrong because authenticated users may still access resources they are not allowed to use

## Quick Verification
```bash
# Confirm a reusable server-side authorization guard/helper exists
rg -n --glob '*.py' 'def (require_role|check_server_side_admin|has_required_role)\b|@require_role\(' .

# Find likely unguarded dangerous authorization decisions that trust client-controlled role/admin fields
rg -n --glob '*.py' '(request\.(headers|get_json\(\)|args|form|cookies).*(X-User-Role|role|is_admin|permissions)|==\s*["'"'"']admin["'"'"'])' .

# Build/test with common Python toolchains across project types
python -m compileall .
pytest -q
```