---
name: secure-cross-origin-resource-sharing
description: "Harden JavaScript CORS handling and CSRF defenses for browser-facing services. Use when code emits CORS headers, trusts Origin, or allows cookie-authenticated cross-origin requests."
---

# Secure cross origin resource sharing (CORS)

## What This Skill Does
This skill fixes insecure CORS handling that can enable CSRF-like abuse, private data exposure, or unsafe cross-origin state changes. It separates CORS from authentication and authorization, adds CSRF validation for cookie-authenticated state-changing requests, and replaces permissive or reflective CORS logic with a centralized deny-by-default policy that uses exact origin allowlists, method/header validation, bounded caching, and safe credential handling.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code reflects `req.headers.origin` into `Access-Control-Allow-Origin`, or uses `origin || '*'` | Replace with centralized CORS logic that parses the origin and compares by exact equality against an allowlist |
| Code uses `Origin` or CORS success as proof of trust for protected `GET`, `POST`, `PUT`, `PATCH`, or `DELETE` endpoints | Require normal authentication and authorization for all non-`OPTIONS` protected requests; do not use `Origin` for auth decisions |
| Cookie-authenticated state-changing routes exist (`POST`, `PUT`, `PATCH`, `DELETE`) without CSRF checks | Add CSRF validation before the state change using a synchronizer token or signed double-submit style token |
| CORS preflight handling allows arbitrary methods or headers | Validate `Access-Control-Request-Method` and `Access-Control-Request-Headers` against explicit allowlists |
| Code already uses exact origin allowlists, rejects wildcard-plus-credentials, and enforces auth + CSRF correctly | No action needed |

## Boundaries

### Can Do
- Replace reflective or partial-match CORS logic with exact allowlist checks using parsed origins
- Add CSRF token verification for cookie-based state-changing requests
- Enforce safe CORS invariants such as no `*` with `Access-Control-Allow-Credentials: true`

### Cannot Do
- Decide which origins, methods, or headers are business-approved without project guidance
- Add full session management, login flows, or complete authorization models
- Protect non-browser clients solely through CORS; CORS is not an API authentication mechanism

## Gotchas
- Using `includes`, `startsWith`, `endsWith`, or loose regex on origins: this accepts attacker-controlled origins like `https://app.example.com.evil.com`
- Sending `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`: browsers reject this and it signals an unsafe policy
- Applying CSRF checks to bearer-token APIs the same way as cookie flows: CSRF is primarily required for browser cookie-authenticated requests, not generic token clients

## Quick Verification
```bash
# Confirm secure helpers/guards exist
rg -n "buildCorsHeaders|isAllowedOrigin|verifyCsrfToken|requiresAuthentication|Access-Control-Allow-Credentials" .

# Find unguarded dangerous CORS patterns and unsafe Origin trust
rg -n "res\.(set|setHeader)\(\s*['\"]Access-Control-Allow-Origin['\"],\s*(req\.headers\.origin|origin\s*\|\|\s*['\"]\*['\"]|origin)\)|Access-Control-Allow-Origin['\"]:\s*(origin|req\.headers\.origin|['\"]\*['\"])\b|Access-Control-Allow-Credentials['\"]:\s*true|req\.headers\.origin|headers\.origin.*(===|==|!=|!==).*auth|includes\(|startsWith\(|endsWith\(" .

# Build + test with the JavaScript project's available toolchain
npm test || yarn test || pnpm test || node --test
```