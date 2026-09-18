---
name: decide-on-the-best-csrf-defense
description: Use when Python code handles state-changing requests with browser-managed cookies or sessions and must choose and apply the correct CSRF defense.
---
# Decide on the best CSRF defense for your application

## What This Skill Does
This skill helps an agent identify Python application flows that are exposed to Cross-Site Request Forgery (CSRF) and choose the right protection based on how requests are authenticated and delivered. It applies synchronizer tokens for server-rendered dynamic pages, double submit cookies for same-origin simple/browser-submittable requests, or strict CORS validation for cross-origin state-changing requests, while also hardening cookies with `SameSite` and preventing token-bearing responses from being cached.

## Decision Table
| Situation | Action |
|-----------|--------|
| State-changing endpoint does not use browser-managed auth cookies or sessions | No CSRF change needed |
| Server-rendered dynamic form/page submits a state-changing request | Apply synchronizer token bound to the session and validate it centrally |
| Same-origin state-changing request can be sent as an HTML form or simple request and synchronizer tokens do not fit | Apply double submit cookie with exact token comparison |
| Cross-origin frontend must send state-changing requests | Enforce secure CORS with explicit allowed origins, methods, and headers; reject unknown origins |
| Session or CSRF cookies are used for same-domain flows | Set `SameSite="Lax"` by default, or `Strict` only if cross-site navigations are not needed |

## Boundaries

### Can Do
- Add Python decision logic that enables CSRF protection only for state-changing requests using browser-managed authentication
- Implement synchronizer token or double submit cookie validation using `secrets.compare_digest`
- Harden session and CSRF cookie settings and add non-cache headers to token-bearing responses

### Cannot Do
- Prove business intent for whether an endpoint truly changes backend state
- Safely use wildcard CORS or infer allowed origins without explicit application requirements
- Protect clients that authenticate with non-browser tokens where cookies/sessions are not automatically sent

## Gotchas
- Protecting every endpoint the same way: unnecessary CSRF checks on token-auth APIs or safe methods can break valid clients and add noise
- Accepting CSRF tokens from arbitrary query parameters: tokens should come from a hidden form field or dedicated header only, or they are easier to leak
- Using normal equality for token comparison: `==` is the wrong comparison for secrets; use `secrets.compare_digest` for exact constant-time checks

## Quick Verification
```bash
# Confirm a CSRF decision/helper or enforcement path exists
rg -n "select_csrf_strategy|enforce_csrf_for_state_change|validate_synchronizer_token|validate_double_submit_cookie|validate_cors_request" .

# Find potentially unguarded Flask state-changing endpoints that may bypass CSRF validation
rg -n '@app\.route\([^)]*methods=\[(?:[^\]]*"POST"|[^\]]*"PUT"|[^\]]*"PATCH"|[^\]]*"DELETE")[^\]]*\][^)]*\)|request\.(form|get_json)\(' .

# Confirm secure token comparison and cookie hardening are present
rg -n "secrets\.compare_digest|SESSION_COOKIE_SAMESITE|set_cookie\(" .

# Run the project's Python test suite if present
python -m pytest -q
```