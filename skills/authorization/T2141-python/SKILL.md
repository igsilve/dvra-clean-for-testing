---
name: perform-function-level-authorization-in-api
description: Enforce server-side, role- and group-based checks on each admin or sensitive API function to prevent direct request / forced browsing; Use when APIs expose admin actions without consistent function-level authorization.
---

# Perform function level authorization in API

## What This Skill Does
Ensures every administrative or sensitive API function performs centralized, server-side authorization based on users, roles, and groups, denying access by default. It fixes missing function-level authorization that lets attackers directly call admin endpoints (forced browsing) by requiring explicit privileges and consistent checks in abstract/regular controllers before any sensitive logic runs.

## Decision Table
| Situation | Action |
|-----------|--------|
| Admin or sensitive endpoint has no explicit server-side authorization check at function entry | Add a centralized admin-check helper and call it as the first line in that function |
| Project has dedicated admin controllers but no shared authorization base | Introduce an `AdminAbstractController` with a strict `checkAdminAccess` method and make all admin controllers extend it |
| Regular controller includes occasional admin-like actions (e.g., promote user, reset password) | Add a dedicated admin-check function in that controller and invoke it in each admin-like method |
| Authorization decisions vary across controllers (different role names / logic) | Standardize on one role/group model and shared helpers (`isAdminAllowed`, `checkAdminAccess`) reused everywhere |
| User/context is sometimes missing or malformed | Normalize context and enforce deny-by-default (treat any missing/invalid user/attributes as unauthorized/forbidden) |
| Code already calls a robust, centralized, deny-by-default authorization helper on every admin function | No action needed (keep existing pattern) |

## Boundaries

### Can Do
- Detect when admin or sensitive API functions lack explicit server-side authorization checks.
- Introduce/extend an abstract admin controller with a centralized `checkAdminAccess` that uses roles and groups and fails closed.
- Add per-function admin checks in regular controllers that host administrative behaviors.
- Refactor scattered conditional checks into a single reusable helper that denies-by-default on missing or invalid user context.

### Cannot Do
- Redesign or harden the entire authentication mechanism (e.g., token issuance, identity proof); this focuses on authorization at function level.
- Infer correct business roles/groups or privilege mappings without guidance from existing code/config or comments.
- Guarantee that every sensitive function is identified when business logic is deeply obfuscated or misnamed (may need human review).
- Fix broader issues like insecure transport (HTTP instead of HTTPS) or broken session management.

## Gotchas
- Forgetting to call the check at the start of every admin function: Adding a helper but only using it on some methods leaves bypass paths; always invoke the check as the first line of each admin/sensitive function.
- Relying on client-side indicators (e.g., `isAdmin` flag in request body/query) instead of server-side roles/groups: Attackers can forge these; always derive authorization from trusted server-side user context.
- Allowing on error or missing data: Treating “no user”, parse failures, or missing `roles/groups` as allowed is dangerous; the helper must deny in all ambiguous or error cases.
- Mixing different role names/rules across controllers: Inconsistent rules cause accidental privilege; centralize role/group constants and reuse the same helper everywhere.

## Quick Verification
```bash
# 1. Run tests (or app) for the fixed example
node app_fix_javascript_code.js alice   # non-admin: should get UNAUTHORIZED/FORBIDDEN style message
node app_fix_javascript_code.js bob     # admin: should be able to perform admin action

# 2. Manual HTTP checks (assuming Express app on localhost:3000)
# Non-admin calling admin endpoint (should be 401/403)
curl -i "http://localhost:3000/admin/deleteUser?username=alice&target=bob"

# Admin calling admin endpoint (should succeed)
curl -i "http://localhost:3000/admin/deleteUser?username=bob&target=alice"

# 3. Grep for unprotected admin functions (heuristic)
rg "admin" . | rg -v "checkAdminAccess|ensureAdmin|isAdminAllowed"
```