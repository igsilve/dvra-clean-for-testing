---
name: t2277-test-to-confirm-the-use-of-an-account-and-identity-managem
description: Confirm that accounts and identities for this service are managed through the organization's identity management system.
---

### Task T2277: Test to confirm the use of an account and identity management system (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2277](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2277/)
**Priority:** 7

**Guidance:** Verification means showing that account creation, modification and deprovisioning for this service flow through the central identity system, with joiner-mover-leaver events reflected automatically and periodic access reviews recorded.

**Why Not Code-Fixable:**
- Searched: app/init.py, app/apis/auth/services/register_user_service.py, app/apis/users/
- Found: Accounts are created locally by the seeding routine and the public /register endpoint; there is no connection to a central identity system to verify.
- Missing: The identity management system integration itself, plus access-review evidence and deprovisioning records.
- Conclusion: The verification has no target until identity management is adopted; it is an audit activity against a platform this deployment does not yet use.

**Recommended Action:** The identity and access management team should perform this verification once accounts for the service are sourced from the central identity system.

**Status:** Documented
