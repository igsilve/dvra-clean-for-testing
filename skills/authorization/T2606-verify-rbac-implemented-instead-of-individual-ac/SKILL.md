---
name: t2606-verify-rbac-implemented-instead-of-individual-accounts
description: Verify that infrastructure access is granted by role rather than by individual account.
---

### Task T2606: Verify RBAC implemented instead of individual accounts (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2606](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2606/)
**Priority:** 10

**Guidance:** Verification means enumerating the accounts on the database and host platforms, confirming each maps to a role rather than a person or a shared secret, and producing a current entitlement report.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/config.py, app/db/session.py
- Found: A single shared PostgreSQL account, `admin`, is used for all application access.
- Missing: Role definitions to verify against and an entitlement reporting mechanism.
- Conclusion: The verification depends on infrastructure role definitions that do not yet exist and are managed outside this repository.

**Recommended Action:** The database administration team should produce the entitlement report once roles are defined.

**Status:** Documented
