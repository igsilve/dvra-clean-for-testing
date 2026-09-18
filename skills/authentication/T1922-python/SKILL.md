---
name: use-secure-oauth-2-0-and-openid-connect-integration
description: Use dedicated OAuth 2.0/OIDC client integrations and validated token claims instead of manual callback or identity handling. Use when Python code manually processes OAuth/OIDC flows or trusts request-supplied identity data.
---

# Use secure OAuth 2.0 and OpenID Connect integration

## What This Skill Does
This skill fixes improper access control and insecure authentication flow handling in Python applications that integrate with OAuth 2.0 or OpenID Connect. It replaces manual authorization URL building, callback parsing, token handling, and identity extraction with a dedicated client integration such as Authlib, keeps provider configuration fixed on the server, and ensures identity and authorization decisions come only from validated token results and claims rather than raw request parameters.

## Decision Table
| Situation | Action |
|-----------|--------|
| Callback handlers read `request.args`, `request.GET`, `request.query_params`, `request.form`, or similar for `access_token`, `code`, `state`, `user`, `sub`, or `email` | Apply this fix |
| Python code manually handles OAuth/OIDC callback exchange instead of using a client library | Replace with a dedicated integration such as `authlib.integrations.*` and use `authorize_access_token()` |
| Code uses identity claims for login or profile data | Read claims only from the validated token result or `userinfo`, not directly from the request |
| Authorization checks use only token existence but do not compare `sub` or scopes to the requested resource | Add claim and scope checks before returning protected data |
| Code already uses a dedicated client integration, fixed provider config, and validated claims for identity and authorization | No action needed |

## Boundaries

### Can Do
- Replace manual OAuth/OIDC callback handling with a dedicated Python client integration
- Move identity parsing to validated token or `userinfo` results returned by the client library
- Add subject and scope checks so valid tokens cannot access unauthorized resources

### Cannot Do
- Choose or provision the correct identity provider, client registration, or provider-side policy
- Guarantee security if downstream code still trusts raw request data after callback validation
- Infer missing business authorization rules when the application does not define required scopes or ownership rules

## Gotchas
- Treating callback parameters as authenticated data: `code`, `state`, `access_token`, `user`, `sub`, and `email` in the request are attacker-controlled until the client integration validates them
- Using OIDC identity claims for authorization without scope or ownership checks: authentication data identifies the caller but does not by itself grant access to every resource
- Mixing manual JWT or ID token decoding with client-library flow handling: this bypasses built-in validation paths and often skips issuer, audience, nonce, or state checks

## Quick Verification
```bash
# Confirm a secure OAuth/OIDC client integration path exists
rg -n "authorize_access_token\(|create_client\(|from authlib\.integrations" .

# Find unguarded manual callback/identity handling from request input
rg -n "request\.(args|get_json|form|values|GET|POST|query_params).*(access_token|code|state|user|sub|email)|access_token\s*=\s*request\.|user(info)?\s*=\s*request\." .

# Find places that introspect or accept tokens but may skip subject/scope authorization checks
rg -n "introspect_token\(|Authorization|Bearer|scope|claims\.get\(\"sub\"\)|requested_user" .

# Generic Python build/test verification
python -m compileall .
python -m unittest discover
pytest -q
```