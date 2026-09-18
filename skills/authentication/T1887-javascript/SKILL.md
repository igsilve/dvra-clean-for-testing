---
name: decide-on-the-right-oauth-2-0-flow-for-your-application
description: "Select and enforce safe OAuth 2.0 flows, PKCE, token validation, and scope checks for JavaScript apps. Use when OAuth flow choice or token-based authorization may break access control."
---
# Decide on the right OAuth 2.0 flow for your application

## What This Skill Does
This skill fixes authorization weaknesses caused by choosing the wrong OAuth 2.0 flow or trusting tokens before proper validation. It adds fail-closed flow selection, forbids Implicit Grant, requires Authorization Code + PKCE with `S256` for end-user apps that can use it, uses Device Authorization Grant for constrained-input public clients, limits Client Credentials to confidential machine-to-machine clients, blocks secrets in public clients, and ensures validated token claims and exact scope checks are used before access is granted.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code selects or accepts `implicit` as an OAuth flow | Reject it and replace with `authorization_code_pkce_public`, `authorization_code_pkce_confidential`, or `device_flow` based on client type and device constraints |
| End user is involved and client is public without constrained input | Apply Authorization Code flow with PKCE and require `code_challenge_method: 'S256'` |
| End user is involved and client is public with constrained input | Use Device Authorization Grant and fail closed on any other flow |
| No end user is involved | Allow `client_credentials` only for confidential clients; reject public clients |
| Code already validates tokens with allowed algorithms and enforces exact required scopes | No action needed |

## Boundaries

### Can Do
- Add or tighten JavaScript flow-selection logic that rejects mismatched OAuth client/flow combinations
- Remove exposed public client secrets or private keys and enforce PKCE `S256`, `state`, and scope checks
- Add local token validation gates before authorization decisions and deny access when validation or scope checks fail

### Cannot Do
- Prove the configured issuer, audience, redirect URIs, or key material are correct for your identity provider
- Safely implement browser refresh-token storage where the platform does not provide secure storage
- Replace a full OAuth client or authorization server integration without project-specific design decisions

## Gotchas
- Treating `client_credentials` as a shortcut for user login: wrong because it is only for confidential clients when no end user is involved
- Allowing caller input to override `response_type`, PKCE method, or required parameters: wrong because it can silently downgrade the flow or disable protections
- Checking scopes before token verification or by substring matching token text: wrong because unvalidated claims must not drive authorization

## Quick Verification
```bash
# Confirm guard functions and secure checks exist
rg -n "selectOAuthFlow|implicit_flow_forbidden|authorization_code_pkce_public|authorization_code_pkce_confidential|device_flow|client_credentials|code_challenge_method['\"]?\s*:\s*['\"]S256['\"]|jwt\.verify|hasRequiredScope|normalizeScopes" .

# Find unguarded dangerous patterns that bypass the fix
rg -n "flow\s*:\s*['\"]implicit['\"]|requestedFlow\s*===\s*['\"]implicit['\"]|clientSecret\s*:\s*['\"][^'\"]+['\"]|privateKey\s*:\s*['\"][^'\"]+['\"]|access_token=|token\.indexOf\(['\"]admin['\"]\)|jwt\.decode\(|jsonwebtoken\.decode\(" .

# Build + test using the JavaScript project toolchain when available
npm test
```