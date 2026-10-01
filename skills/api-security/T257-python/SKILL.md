---
name: secure-cross-origin-resource-sharing
description: Use when Python code treats CORS or the Origin header as access control, exposes private resources cross-origin, or skips CSRF protection on authenticated state-changing requests.
---
# Secure cross origin resource sharing (CORS)

## What This Skill Does
This skill fixes Python code that misuses CORS as an authorization mechanism, trusts the `Origin` header for private access, returns permissive `Access-Control-Allow-*` headers on non-public endpoints, or skips CSRF validation for authenticated state-changing requests. Apply it to separate public, private, and explicitly shareable cross-origin resources; require normal authentication and authorization for private functionality; enforce CSRF on authenticated state changes; and only emit CORS headers when the origin, method, and requested headers exactly match approved policy.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code reads `request.headers.get("Origin")` or `request.headers["Origin"]` to allow access to private functionality | Remove Origin-based access control; require normal authentication/authorization and keep behavior the same for same-origin or no-Origin requests |
| A private endpoint returns `Access-Control-Allow-*` headers | Remove CORS headers unless the endpoint is explicitly designed for cross-origin sharing |
| A public unauthenticated resource is intentionally shareable across origins | Return `Access-Control-Allow-Origin: *` only if no credentials are used |
| A shareable cross-origin endpoint needs controlled access | Exact-match the full `Origin` against a whitelist and validate requested method and headers before returning CORS headers |
| An authenticated state-changing request (`POST`, `PUT`, `PATCH`, `DELETE`) relies only on session cookies | Add CSRF validation and do not treat a trusted origin as a replacement for CSRF protection |

## Boundaries

### Can Do
- Replace Origin-based authorization decisions with server-side authentication and authorization checks
- Tighten Python CORS handling for Flask-style request/response code, including exact origin, method, and header checks
- Add or preserve CSRF validation for authenticated state-changing requests

### Cannot Do
- Infer the correct business whitelist of allowed origins without project-specific requirements
- Prove an endpoint is truly public and safe for wildcard CORS without understanding its data sensitivity and auth model
- Guarantee framework-wide CSRF coverage if the application uses custom middleware, multiple frameworks, or nonstandard request handling

## Gotchas
- Using substring or suffix origin checks: `endswith`, `startswith`, `in`, or regex-style matching can allow attacker-controlled origins like `https://trusted.example.com.attacker.test`
- Combining `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`: browsers reject this and it signals a broken policy for credentialed flows
- Treating `OPTIONS` as an authorization bypass: preflight should only negotiate CORS policy, not grant access to private functionality or replace auth/CSRF checks

## Quick Verification
```bash
# Confirm secure CORS/CSRF code paths exist
rg -n 'Access-Control-Allow-Origin|Access-Control-Allow-Credentials|Access-Control-Allow-Methods|Access-Control-Allow-Headers|Access-Control-Max-Age|validate_csrf_token|X-CSRF-Token|compare_digest|require_authenticated_user' .

# Find likely unguarded dangerous patterns: Origin-based access control, permissive CORS on private code, and state-changing handlers missing CSRF validation
rg -n 'request\.headers\.get\(["'"'"']Origin["'"'"']|request\.headers\["Origin"\]|Access-Control-Allow-Origin["'"'"']?\s*[:=]\s*["'"'"']\*["'"'"']|methods=\[[^]]*(POST|PUT|PATCH|DELETE)[^]]*\]' .

# Build/test using generic Python tooling
python -m compileall .
python -m pytest -q
```