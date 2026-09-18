---
name: t2105-enforce-the-use-of-client-certificate-bu
description: Enforce the use of client certificate bundles for unprivileged users to access UCP (Docker)
---

# T2105: Enforce the use of client certificate bundles for unprivileged users to access UCP (Docker)

**Category:** IN
**SD Elements:** [T2105](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2105/)
**Priority:** 7

### Task T2105: Enforce the use of client certificate bundles for unprivileged users to access UCP (Docker) (DOCUMENTATION ONLY)

**Guidance:** Provide unprivileged users with client certificate bundles for connecting to UCP manager nodes and communicating with a UCP cluster so that their access rights are controlled via the built-in role-based access control (RBAC) model.

With the use of UCP client certificate bundles, you do not need to include standard users in the "docker" security group and instead, you can facilitate user access to the cluster via RBAC.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
