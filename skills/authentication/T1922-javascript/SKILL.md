---
name: use-secure-oauth-2-0-and-openid-connect-integration
description: "Harden JavaScript OAuth 2.0/OIDC login and bearer-token authorization flows against improper access control. Use when code builds auth requests, validates access or ID tokens, trusts caller identity, or stores OIDC transaction/session state."
---
# Use secure OAuth 2.0 and OpenID Connect integration

## What This Skill Does
This skill fixes improper access control in JavaScript applications that use OAuth 2.0 or OpenID Connect by replacing caller-supplied identity and weak flow handling with transaction-bound authorization code + PKCE, strict bearer token extraction, full access token and ID token validation, exact scope checks, and minimal session-bound OIDC state handling. Apply it when code accepts `Authorization` headers, processes login callbacks, validates JWTs, stores `state`/`nonce`, or authorizes actions from untrusted request fields.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code trusts `req.query.user`, `req.body.user`, headers, or other caller-supplied identity values for authorization | Replace with validated access-token claims such as `sub` and exact scope checks |
| User-facing OAuth/OIDC login flow is being implemented | Use Authorization Code Grant with PKCE and generate per-transaction `state`, `nonce`, and `code_verifier` |
| Machine-to-machine token acquisition is used | Use `client_credentials` only, and request only allowlisted scopes |
| Resource server accepts bearer tokens or JWTs | Add strict `Bearer` parsing and validate algorithm, issuer, audience, expiry, not-before, subject, and token type before authorizing |
| Code already validates access tokens/ID tokens, compares `state`/`nonce` exactly, and authorizes from validated claims only | No action needed |

## Boundaries

### Can Do
- Add secure OAuth 2.0/OIDC helpers for authorization requests, token validation, ID token validation, and scope enforcement
- Replace caller-controlled identity checks with authorization based on validated token claims
- Tighten OIDC session handling by binding and clearing `state`, `nonce`, and related transaction data

### Cannot Do
- Choose your real issuer URLs, client IDs, signing keys, or JWKS configuration without trusted deployment input
- Prove a third-party identity provider is securely configured beyond the application's own validation and allowlists
- Safely preserve insecure OAuth flows that the application does not explicitly require

## Gotchas
- Accepting loose authorization headers: parsing anything other than a single exact `Bearer <token>` value can let malformed or duplicate credentials bypass checks
- Using `jwt.decode()` instead of `jwt.verify()`: decoding reads attacker-controlled claims without validating signature, issuer, audience, or expiry
- Treating scopes as substring matches: checking `"admin"` inside `"superadmin"` or raw scope strings grants permissions that were never actually assigned

## Quick Verification
```bash
# Confirm secure OAuth/OIDC guard helpers or validation logic exist
rg -n 'extractBearerToken|validateAccessToken|authenticateRequest|validateIdTokenForLogin|buildAuthorizationCodePkceRequest|state|nonce|code_challenge|jwt\.verify' .

# Find unguarded dangerous patterns that trust caller input or decode tokens without verification
rg -n 'req\.(query|body|params)\.(user|sub|role)|jwt\.decode\(|authorizationHeader\.match\(/.*Bearer.*\)/|req\.headers\.authorization(?!.*authenticateRequest)' .

# Build + test using whichever JavaScript toolchain the project provides
npm test || yarn test || pnpm test || node --test
```