---
name: t1889-secure-the-configuration-of-the-authorization-server
description: Harden the configuration of the authorization server that issues tokens for this application.
---

### Task T1889: Secure the configuration of the authorization server (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1889](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1889/)
**Priority:** 7

**Guidance:** The authorization server should pin its supported grant types and algorithms, register exact redirect URIs, disable implicit and resource-owner-password grants, enforce short access-token lifetimes with rotating refresh tokens, and publish its keys through a rotating JWKS endpoint.

**Why Not Code-Fixable:**
- Searched: app/apis/auth/, app/config.py, pyproject.toml
- Found: The application signs its own HS256 tokens in app/apis/auth/utils/utils.py; there is no external authorization server and no OAuth client configuration.
- Missing: An identity provider to configure, its client registrations, and the operational ownership of its settings.
- Conclusion: There is no authorization server in this deployment to configure; the requirement applies to an identity platform that would be adopted at the architecture level.

**Recommended Action:** The identity and access management team should own the authorization server configuration baseline if and when this service federates authentication.

**Status:** Documented
