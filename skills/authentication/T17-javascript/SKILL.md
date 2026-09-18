---
name: do-not-only-rely-on-client-side-authorization
description: "Enforce server-side authorization for protected JavaScript reads and mutations. Use when code trusts client-controlled roles, flags, route guards, or raw resource IDs for access control."
---
# Do not only rely on client-side authorization

## What This Skill Does
This skill fixes client-side enforcement of server-side security by moving authorization decisions to trusted server code. It replaces checks based on `req.body`, `req.query`, UI flags, local storage, or hidden routes with a centralized server-side authorization function that uses session-derived identity, scopes resource access by owner or tenant on the server, and denies unknown or missing inputs by default before protected data is returned or state is changed.

## Decision Table
| Situation | Action |
|-----------|--------|
| Authorization depends on `req.body.isAdmin`, `req.query.role`, client flags, route guards, or local storage values | Replace with server-side `buildTrustedUser(...)` from session/auth context and call `authorize(user, action, resource)` |
| Protected read or write accepts a raw resource ID such as document, account, or file ID | Scope the server lookup by both resource ID and authenticated user ownership/tenant rules using parameterized queries or ORM filters |
| A mutation updates or deletes sensitive state directly | Wrap the mutation in a server-side function that checks `authorize(...)` first and denies by default |
| Multiple handlers implement ad hoc permission logic | Centralize checks in one `authorize(user, action, resource)` or `enforceAuthorization(...)` function and reuse it at every entry point |
| Code already uses trusted session identity, server-side resource scoping, and deny-by-default authorization | No action needed |

## Boundaries

### Can Do
- Replace client-controlled authorization decisions with server-side checks based on trusted session identity
- Add centralized authorization guards for reads, updates, deletes, exports, admin actions, and background-triggered operations
- Scope resource access on the server with parameterized SQL or safe ORM filtering by both resource ID and user scope

### Cannot Do
- Create a full authentication system if the application has no trusted identity source at all
- Infer correct business authorization rules when ownership, tenant, or role requirements are undefined
- Prevent client-side UX hints from being bypassed; it only ensures the server denies unauthorized access

## Gotchas
- Checking client role fields before calling the server guard: this is wrong because `req.body.role`, `req.query.role`, and similar inputs are attacker-controlled
- Authorizing once but loading the resource without scope constraints: this is wrong because guessed IDs can still expose another user's object if the query is only filtered by `id`
- Allowing unknown actions or missing resource fields to fall through: this is wrong because permissive defaults turn new code paths into silent authorization bypasses

## Quick Verification
```bash
# Confirm the secure server-side guard/wrapper exists
rg -n "function (authorize|enforceAuthorization|buildTrustedUser|getUserFromSession)\b|const (authorize|enforceAuthorization|buildTrustedUser|getUserFromSession)\b" .

# Find unguarded dangerous client-controlled authorization inputs
rg -n "req\.(body|query|params)\.(role|isAdmin|userId)|localStorage\.getItem\(['\"]role['\"]\)|window\.isAdmin|clientRole\s*===\s*['\"]admin['\"]" .

# Build + test with the project's JavaScript toolchain
npm test && npm run build --if-present
```