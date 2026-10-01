---
name: perform-authorization-checks-on-restful-web-services
description: Use when Python code exposes REST endpoints or privileged service methods without server-side authorization by route, HTTP verb, role, or validated token claims.
---
# Perform authorization checks on RESTful web services

## What This Skill Does
This skill fixes insufficient authorization on RESTful web service endpoints by adding server-side authentication and deny-by-default authorization checks at both the HTTP entry point and the underlying business method. Use it when Python code trusts client-supplied role data, allows sensitive routes or verbs without explicit permission checks, or exposes admin and third-party API operations without validated identity and claim checks.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Flask or similar REST handler performs sensitive actions without checking the caller's permissions for the route and HTTP verb | Add a reusable authorization guard that authenticates first, maps permissions by `METHOD:route`, and denies by default |
| Code trusts request headers or request data such as `X-User-Role`, `role`, or `is_admin` for authorization | Replace that logic with server-derived identity from authenticated tokens or sessions |
| A business/service function performs delete, update, admin, or management actions directly | Add a trusted `caller_role` or permission context parameter and enforce authorization again inside the function |
| An endpoint is administrative or management-only | Apply a dedicated admin-only guard instead of a generic authenticated-user check |
| Authorization is already enforced from validated server-side identity at both endpoint and sensitive method | No action needed |

## Boundaries

### Can Do
- Add reusable Python authorization helpers and decorators for route + HTTP verb checks
- Replace client-controlled role checks with server-validated token or session identity
- Enforce admin-only and privileged-operation checks inside service methods as well as REST handlers

### Cannot Do
- Design a full IAM or RBAC model for the whole organization
- Prove every route alias, background entry point, or indirect call path is covered without repository review
- Fix broken authentication, secret management, or token issuance beyond rejecting untrusted or invalid identity data

## Gotchas
- Trusting `X-User-Role` or similar request fields: these are attacker-controlled and cannot be used as proof of privilege
- Checking only the route but not the HTTP verb: `GET:/resource` and `DELETE:/resource` may require different permissions
- Guarding only the endpoint and not the service function: new call paths such as CLI commands, jobs, or internal helpers can bypass the route check

## Quick Verification
```bash
# Confirm secure authorization helpers or admin guards exist
rg -n --glob '*.py' 'def (authenticate_request|require_route_permission|require_admin|require_admin_only|authenticate_third_party_request|delete_user_secure)\b|@require_(route_permission|admin_only)\b'

# Find unguarded dangerous patterns: client-controlled role trust or privileged deletes without secure wrapper usage
rg -n --glob '*.py' 'request\.headers\.get\(("X-User-Role"|'\"'X-User-Role'\"'|"X-User-Role")|delete_user_insecure\(|client_role\s*==\s*["'"'"']admin["'"'"']'

# Basic Python validation across app, library, CLI, and service codebases
python -m compileall .

# Run tests when present
python -m pytest -q
```