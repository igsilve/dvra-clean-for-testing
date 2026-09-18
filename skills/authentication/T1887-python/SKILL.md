---
name: decide-on-the-right-oauth-2-0-flow-for-your-application
description: "Select and enforce safe OAuth 2.0 flows in Python to prevent improper authorization; Use when flow choice, PKCE, client authentication, refresh token use, or grant construction is derived from config, input, or inconsistent logic."
---

# Decide on the right OAuth 2.0 flow for your application

## What This Skill Does
This skill fixes improper authorization caused by selecting unsafe or inconsistent OAuth 2.0 flows in Python. It replaces ad hoc flow selection with one deterministic selector, rejects unsupported flows such as Implicit Grant, requires PKCE with S256 for Authorization Code, restricts client authentication to confidential clients only, blocks refresh token use for browser-based clients, and ensures each token request uses only the exact grant fields allowed for the selected flow.

## Decision Table
| Situation | Action |
|-----------|--------|
| OAuth flow is chosen from config strings, request parameters, or scattered endpoint logic | Add a single `select_oauth_flow(...)` function with an allowlist of `authorization_code_pkce`, `device_flow`, and `client_credentials`; reject anything else |
| End-user client is web, desktop, or mobile and is not a constrained-input device | Use Authorization Code with PKCE and require `code_challenge`, `code_challenge_method="S256"`, and `code_verifier` |
| Public client is browser-based, mobile, or otherwise cannot keep secrets | Do not send `client_secret` or private-key client auth; reject public-client token requests that include secret-based authentication |
| Constrained-input public client needs user authorization | Use Device Flow and require `device_code`; do not fall back to Implicit Grant |
| Code already derives flow from explicit client traits, enforces PKCE, forbids public-client secrets, and gates refresh tokens consistently | No action needed |

## Boundaries

### Can Do
- Centralize OAuth flow selection in a deterministic Python function or policy module
- Enforce PKCE with S256 for Authorization Code flows at authorization and token exchange time
- Split confidential-client and public-client token request construction and reject invalid grant payloads

### Cannot Do
- Prove the identity provider is configured securely server-side if the application never validates its own requests
- Invent secure storage for refresh tokens where the platform cannot protect them
- Determine business authorization scopes or user entitlements beyond enforcing safe flow and grant usage

## Gotchas
- Treating browser or mobile apps as confidential clients: client secrets on end-user devices are exposed and must not be relied on
- Adding PKCE only to the authorization request: token exchange must also require and send the matching `code_verifier`
- Allowing `grant_type` or flow names from runtime input: this reintroduces unsafe flows such as `implicit` or mixed grant payloads

## Quick Verification
```bash
# Confirm the secure selector / guards exist
rg -n "select_oauth_flow|ALLOWED_FLOWS|authorization_code_pkce|device_flow|client_credentials|may_use_refresh_tokens|build_grant_payload|code_challenge_method[\"']?\s*[:=]\s*[\"']S256[\"']" .

# Find unguarded or unsafe OAuth usage that may bypass the fix
rg -n "implicit|response_type[\"']?\s*[:=]\s*[\"']token[\"']|grant_type[\"']?\s*[:=]\s*[\"']implicit[\"']|client_secret\s*=|HTTPBasicAuth\(|grant_type[\"']?\s*[:=]\s*[\"']authorization_code[\"']" .

# Basic Python build check for syntax across app, library, CLI, or service code
python -m compileall .

# Run tests if present
python -m unittest discover -v
```