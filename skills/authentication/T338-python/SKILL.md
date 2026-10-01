---
name: control-access-to-resources-through-user-authentication-and-authorization
description: Use when Python code exposes protected resources or actions without consistent server-side authentication, authorization, ownership checks, step-up verification, or session invalidation.
---
# Control access to resources through user authentication and authorization

## What This Skill Does
This skill fixes improper access control in Python code by adding explicit server-side authentication and authorization before protected data is returned or sensitive actions run. It centralizes checks in reusable guards/helpers, enforces role and ownership validation on each request, requires fresh step-up authentication for high-risk operations, invalidates session state on logout, and uses allowlists for public output so code fails closed instead of trusting client input, route structure, or hidden fields.

## Decision Table
| Situation | Action |
|-----------|--------|
| A function, route, CLI path, or service handler returns protected data without checking the caller identity | Resolve an authenticated principal first and deny by default if authentication fails |
| Code checks only `requested_user_id`/resource ID but not whether the caller owns it or has the required role | Add object-level authorization that verifies both role/permission and ownership before read/write |
| Sensitive operations such as account changes, transfers, or private field access rely on normal login only | Require separate short-lived step-up verification state (for example MFA) before completing the action |
| Service-to-service access uses shared/plaintext secrets or grants broad access after authentication alone | Authenticate each service with a unique server-verified secret hash and check per-action permissions |
| Code already uses centralized auth guards, ownership checks, deny-by-default behavior, and sanitized public output | No action needed |

## Boundaries

### Can Do
- Add reusable Python authorization helpers, guards, or middleware patterns around protected reads and writes
- Enforce role, permission, and ownership checks for user and service callers
- Add session logout invalidation, step-up verification gates, and public-field allowlisting

### Cannot Do
- Invent a complete identity provider, MFA delivery system, or production secret management setup from scratch
- Determine correct business permissions without clues from the application's domain rules
- Guarantee every access path is covered if parts of the system are outside the scanned codebase or use external policy engines

## Gotchas
- Checking authentication but not ownership: authenticated users can still read or modify other users' records, creating IDOR/BOLA issues
- Trusting client-supplied role flags, hidden fields, or URL patterns: authorization must be derived and enforced server-side on every request
- Returning full model dicts by default: even authorized publish/read paths can leak nonpublic fields unless output is explicitly allowlisted

## Quick Verification
```bash
# Confirm authz guard patterns exist somewhere in Python code
rg -n --glob '*.py' 'def (has_.*access|is_allowed|authorize|authenticate_requester|logout|service_get_user_profile|get_public_profile)\b|mfa_verified_at|compare_digest|SESSIONS\.pop\(' .

# Find likely unguarded protected-data access or dangerous direct returns in Python code
rg -n --glob '*.py' 'return\s+USER_PROFILES\.get\(|return\s+dict\(full_profile\)|print\(\s*profile\s*\)|private_notes' .

# Run the project's Python test suite with the most common available toolchain
python -m pytest -q || python -m unittest discover -v
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T338 in this project because of its survey answers. Copied verbatim from SD Elements.

### Prevent untrusted parties from accessing admin interfaces in applications

Use the following guidelines for preventing untrusted parties from accessing administrative interfaces:

-Restrict non-admin users from accessing information or features they do not need.

-Use secure interface elements for making certain features or information visible or invisible and editable or uneditable for non-admin users based on their needs. 

-Restrict admin areas from being accessible from a single IP. Consider keeping the admin interface on a private subnet and off the public internet.

-Use second level authentication and consider using client SSL certificates for accessing admin areas. 

-Only allow access from trusted domains and IPs. This can be done by adding a check to a basic HTTP pipeline or by blocking untrusted IPs in access configuration files.

-Reissue the session ticket when moving between admin and normal users.

### Authorization, MDS2-2013

The answers to these questions are directly affected by the characteristics of the chosen authorization/authentication system:

- 3-1 Can the device prevent access to unauthorized users through user login requirements or other mechanism?

     - Other mechanisms may include use of smart cards, password-generating-tokens, device-specific certificates (e.g. PKI authentication of users/devices), etc. Note that in order to effectively prevent unauthorized access to resources you should complete the authentication/authorization related security tasks that are linked to this section in the compliance regulation report.
 
- 3-2	Can users be assigned different privilege levels within an application based on 'roles' (e.g., guests, regular users, power users, administrators, etc.)?

     - This is affected by the authorization model that is adopted. If you are using an RBAC model, the answer is yes.
