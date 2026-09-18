---
name: use-correct-http-methods-for-state-changing-operations
description: Use when JavaScript code allows GET or HEAD to create, update, delete, log out, or otherwise change server-side state; move mutations to non-safe methods and ensure they require CSRF protection.
---

# Use the Correct HTTP Methods for State-Changing Operations

## What This Skill Does
This skill fixes CSRF exposure caused by treating `GET` or `HEAD` as state-changing operations. In JavaScript applications, it finds handlers, route definitions, and helper functions where safe methods perform mutations such as logout, session invalidation, create/update/delete actions, or persistent state changes, then moves those operations to `POST`, `PUT`, `PATCH`, or `DELETE`. It also adds method classification and fail-closed guards so safe methods stay read-only and non-safe methods remain eligible for CSRF protection.

## Decision Table
| Situation | Action |
|-----------|--------|
| A `GET` or `HEAD` route logs out users, destroys sessions, resets data, deletes data, or updates state | Move the mutation to `POST`, `PUT`, `PATCH`, or `DELETE`; return `405` or no-op on `GET`/`HEAD` |
| Route registration is centralized or can be wrapped | Add a route-definition guard that rejects mutating handlers bound to `get` or `head` |
| The code classifies request methods for security checks | Explicitly treat only safe methods as read-only and require CSRF protection for all other methods |
| A `GET` or `HEAD` request includes mutation-like inputs such as `action=logout` or unexpected bodies | Reject the request and do not perform any state change |
| Code already keeps `GET`/`HEAD` read-only and protects non-safe methods with CSRF validation | No action needed |

## Boundaries

### Can Do
- Change JavaScript route handlers and helper functions so mutations use `POST`, `PUT`, `PATCH`, or `DELETE`
- Add method guards such as `isSafeMethod`, `methodRequiresCsrfProtection`, or route-registration validation
- Add explicit rejection for `GET` or `HEAD` calls that attempt logout, session destruction, updates, deletes, or other mutations

### Cannot Do
- Implement complete CSRF token issuance and client integration for every framework automatically
- Infer business intent when a handler has mixed read and write behavior without code evidence
- Guarantee protection if state changes still occur in downstream code paths triggered by nominally read-only handlers

## Gotchas
- Allowing logout on `GET` because it seems harmless: logout changes authentication state and is still a CSRF-sensitive mutation
- Moving a route from `GET` to `POST` but leaving helper functions to mutate on `GET`: direct calls, CLI paths, tests, or background invocations can still preserve the bug
- Treating all non-`GET` methods as automatically protected: changing the verb is not enough unless non-safe methods also go through CSRF validation

## Quick Verification
```bash
# Confirm secure method-classification or guard helpers exist
rg -n "isSafeMethod|methodRequiresCsrfProtection|ensureNonSafeMethodForMutation|rejectSuspiciousSafeMethodMutations|defineRoute" .

# Find unguarded dangerous patterns where GET/HEAD still appears to perform mutations
rg -n "app\.(get|head)\s*\([^)]*(logout|reset|delete|destroy|update|invalidate)|router\.(get|head)\s*\([^)]*(logout|reset|delete|destroy|update|invalidate)|req\.session\.destroy\s*\(|\.destroy\s*\(|\b(balance|state|session|user)\b\s*=" .

# Build if a build script exists, then run tests if present
npm run build --if-present && npm test --if-present
```