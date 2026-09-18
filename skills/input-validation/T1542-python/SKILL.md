---
name: use-correct-http-methods-for-state-changing-operations
description: Use when Python code allows GET or HEAD to trigger creates, updates, deletes, logout, or other server-side mutations; enforce method gating and return 405 for wrong methods.
---

# Use the correct HTTP methods for making state-changing operations

## What This Skill Does
This skill fixes CSRF-prone request handling where Python code lets `GET` or `HEAD` perform state changes such as create, update, delete, logout, token invalidation, or balance transfers. It moves mutating logic behind `POST`, `PUT`, `PATCH`, or `DELETE`, adds an explicit request-method gate before parsing input or calling mutators, and ensures unsupported methods fail with `405 Method Not Allowed` so read-only requests stay free of side effects.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Flask/Django/FastAPI/Python HTTP handler uses `GET` or `HEAD` and then calls a mutating function or writes session/database state | Move the mutation to a `POST`/`PUT`/`PATCH`/`DELETE` route and reject `GET`/`HEAD` with `405` |
| A handler reads mutation input from `request.args`, query strings, or URL parameters for an action like transfer, logout, delete, or update | Replace query-driven mutation with form or body input on a non-GET method |
| Code parses request data before checking `request.method` | Add method gating first, then parse input, then run business logic |
| The framework route is already limited to `POST`/`PUT`/`PATCH`/`DELETE` and `GET`/`HEAD` handlers are read-only | No action needed |
| A state-changing endpoint is exposed via hyperlink, image URL, prefetchable URL, or redirect target | Replace it with a form or API call using the intended non-GET method |

## Boundaries

### Can Do
- Refactor Python request handlers so `GET` and `HEAD` are read-only
- Add explicit method checks such as `if request.method != "POST": abort(405)`
- Separate read handlers from mutating handlers and route writes through `POST`/`PUT`/`PATCH`/`DELETE`

### Cannot Do
- Guarantee CSRF safety by method changes alone; mutating non-GET routes may still need CSRF tokens or origin checks
- Infer full business semantics for choosing between `POST`, `PUT`, `PATCH`, and `DELETE` without application context
- Prove the absence of side effects hidden inside downstream helpers, ORMs, caches, or audit hooks without code review

## Gotchas
- Allowing `HEAD` because "it has no body": wrong, `HEAD` must follow the same no-state-change rule as `GET`
- Only changing the route decorator and leaving shared mutating logic callable from a read path: wrong, `GET` code paths can still trigger writes indirectly
- Returning a redirect instead of `405` for wrong methods on a mutating endpoint: wrong, the unsafe method should be rejected explicitly and state must remain unchanged

## Quick Verification
```bash
# Confirm method gating or non-GET route restrictions exist in Python handlers
rg -n 'request\.method\s*!=\s*"(POST|PUT|PATCH|DELETE)"|abort\(405\)|methods\s*=\s*\[(?:[^]]*"(POST|PUT|PATCH|DELETE)"[^]]*)\]' .

# Find likely unguarded dangerous patterns: GET/HEAD routes or query args feeding state-changing actions
rg -n '@app\.route\(.*methods\s*=\s*\[[^]]*"(GET|HEAD)"[^]]*\].*\)|request\.args\.get\(|request\.GET\[|request\.query_params|request\.method\s*==\s*"GET"' .

# Build + test with generic Python toolchain commands
python -m compileall .
python -m pytest -q
```