---
name: t340-use-an-account-and-identity-management-system
description: Source accounts and identities for this service from a central account and identity management system.
---

### Task T340: Use an account and identity management system (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T340](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T340/)
**Priority:** 7

**Guidance:** Identity lifecycle should be owned centrally: provisioning, role assignment, recertification and deprovisioning driven by the identity system rather than by application-local records.

**Why Not Code-Fixable:**
- Searched: app/init.py, app/db/models.py, app/apis/auth/
- Found: A local users table is the sole identity store, seeded at startup and extended through self-registration.
- Missing: A central identity platform, a provisioning connector and an authoritative source for role assignment.
- Conclusion: Adopting central identity management is a platform decision requiring systems outside this repository.

**Recommended Action:** The identity and access management team should own selection and rollout of the account and identity management system.

**Status:** Documented
