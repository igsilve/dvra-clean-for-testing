---
name: use-anti-cross-site-request-forgery-csrf-tokens
description: Enforce CSRF tokens on state-changing HTTP requests to prevent Cross-Site Request Forgery; use when endpoints rely on browser cookies or auth headers without CSRF defenses.
---

# Use anti-Cross-Site Request Forgery (CSRF) tokens

## What This Skill Does
Adds or strengthens CSRF token protections on state-changing endpoints. It ensures each authenticated user/session gets an unpredictable token, that the token is embedded in client requests (form fields or headers), and that every unsafe request validates the token before performing any state change.

## Decision Table
| Situation | Action |
|-----------|--------|
| State-changing endpoint (POST/PUT/PATCH/DELETE) relies only on cookies/session for auth and has no CSRF token check | Integrate a CSRF library, generate per-session token, embed in form/JS, and validate on every unsafe request |
| HTML form performs account or data changes and has no hidden CSRF field | Add hidden `csrf_token` input populated from a server-side generator, and verify it server-side before processing |
| SPA or AJAX calls modify server state and send only cookies | Expose CSRF token via safe endpoint or non-HttpOnly cookie, send it in a custom header (e.g., `X-CSRF-Token`), and validate it on the server |
| Framework already provides CSRF middleware (e.g., Django, Rails, Spring Security) and it is enabled on the route | No action needed; only verify the route is not exempted and that templates include the framework's CSRF helpers |
| Endpoint is read-only (idempotent GET) and does not change server-side state | No CSRF token required; leave as-is unless GET has side effects |

## Boundaries

### Can Do
- Detect missing CSRF tokens on clearly state-changing endpoints that trust browser cookies or authentication headers.
- Add secure token generation and validation using libraries like `itsdangerous` or framework-native CSRF support.
- Refactor forms and handlers so that tokens are consistently embedded and validated before sensitive operations.

### Cannot Do
- Guarantee protection if the framework's own CSRF middleware is misconfigured, disabled elsewhere, or bypassed via alternate routes.
- Fix broader authentication/session design issues (weak session IDs, missing HTTPS, missing SameSite) beyond ensuring tokens exist and are checked.
- Decide business-specific exemptions (e.g., public APIs, webhook endpoints) without human input about intended usage and clients.

## Gotchas
- Relying only on a CSRF token cookie: If the server checks only a cookie value, a cross-site request will send it automatically; you must also require the token in a header or body field that an attacker cannot set with a simple cross-site form.
- Putting CSRF tokens in URLs (query strings): Tokens can leak via logs, browser history, and Referer headers; use hidden form fields or headers instead.
- Protecting only some state-changing routes: Leaving even one POST/PUT/PATCH/DELETE endpoint without CSRF validation can still allow impactful attacks; apply checks consistently across all state-changing handlers.

## Quick Verification
```bash
# 1) Start the fixed Flask demo app
export FLASK_APP=app_fixed.py
flask run

# 2) In one terminal, log in via browser at http://127.0.0.1:5000/login
#    Then open http://127.0.0.1:5000/transfer and capture the csrf_token value.

# 3) Test missing/invalid token is rejected
curl -i -X POST \
  -H "Cookie: session_id=<your_session_id>; username=<your_username>" \
  -d "to=bob&amount=100" \
  http://127.0.0.1:5000/transfer

# Expect: HTTP 4xx response or error page indicating invalid/missing CSRF token.

# 4) Test valid token is accepted
curl -i -X POST \
  -H "Cookie: session_id=<your_session_id>; username=<your_username>; csrf_token=<csrf_token_from_app>" \
  -d "to=bob&amount=100&csrf_token=<csrf_token_from_app>" \
  http://127.0.0.1:5000/transfer

# Expect: Success response indicating transfer completed.

# 5) (Optional) Negative test with tampered token
curl -i -X POST \
  -H "Cookie: session_id=<your_session_id>; username=<your_username>; csrf_token=INVALID" \
  -d "to=bob&amount=100&csrf_token=INVALID" \
  http://127.0.0.1:5000/transfer

# Expect: Same failure as the missing/invalid token case.
```