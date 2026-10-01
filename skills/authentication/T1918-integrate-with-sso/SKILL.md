---
name: t1918-integrate-with-sso
description: Federate authentication to the organization's single sign-on provider instead of holding local credentials.
---

### Task T1918: Integrate with SSO (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1918](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1918/)
**Priority:** 9

**Guidance:** Authentication should be delegated to the corporate identity provider over OIDC, with the application consuming validated identity assertions, mapping provider groups to its roles, and retaining no local password store.

**Why Not Code-Fixable:**
- Searched: app/apis/auth/, app/init.py, app/db/models.py
- Found: The service maintains its own users table with locally hashed passwords and issues its own tokens; no identity provider integration exists.
- Missing: A tenant in the identity provider, client registration, group-to-role mapping and a migration plan for existing local accounts.
- Conclusion: SSO adoption is an organizational identity decision requiring provider onboarding and a credential migration, well beyond a change in this repository.

**Recommended Action:** The identity and access management team should decide on SSO adoption and provide the client registration this service would consume.

**Update (this run):** Confirmed still documentation-only. No OIDC or SAML
integration was added, because delegating authentication is a change of identity
authority rather than a code fix: it requires a provider tenant, a registered
client with a redirect URI, an agreed group-to-role mapping, and a migration
path for existing accounts. Implementing a speculative flow against an unknown
provider would add unreviewed authentication code and a second, untested way in.

Current state and what the owning team needs to supply:

- **Local credential store remains authoritative.** `app/db/models.py` holds a
  `users` table with a local password column; `app/apis/auth/` issues the
  service's own HS256 JWTs. Under T7354 those hashes are now argon2id with
  pinned cost parameters, which is the interim control while SSO is undecided.
- **Roles are local.** `UserRole` (`CHEF`, `EMPLOYEE`, `CUSTOMER`) is assigned
  per user in the database. An SSO rollout needs a documented mapping from
  provider groups to these three roles before cutover.
- **Required from IAM:** issuer URL, client ID and secret, JWKS endpoint, the
  claim carrying group membership, and a decision on whether local accounts are
  migrated or run alongside federated ones during transition.

Routed to: identity and access management team, via this countermeasure's
SD Elements record.

**Status:** Documented
