---
name: t2256-authenticate-and-log-all-access-to-registries-containing-s
description: Authenticate and log every access to registries holding this project's images.
---

### Task T2256: Authenticate and log all access to registries containing sensitive or proprietary images (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2256](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2256/)
**Priority:** 8

**Guidance:** Registry access should require an identity, log every pull and push with the identity and image digest, and ship those records to central log storage for review.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: Images are pulled anonymously from a public registry; no private registry or access logging exists.
- Missing: A private registry with authentication and an audit log destination.
- Conclusion: Registry authentication and logging are properties of the registry service, configured outside this repository.

**Recommended Action:** The container platform team should require authentication and enable access logging on the registry.

**Status:** Documented
