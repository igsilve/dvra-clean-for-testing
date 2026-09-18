---
name: t2661-change-insecure-configuration-defaults-a
description: Change insecure configuration defaults and remove unnecessary features
---

# T2661: Change insecure configuration defaults and remove unnecessary features

**Category:** IN
**SD Elements:** [T2661](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2661/)
**Priority:** 9

### Task T2661: Change insecure configuration defaults and remove unnecessary features (DOCUMENTATION ONLY)

**Guidance:** In most cases, the default configuration of a database product or its official Docker image is suitable for development purposes only. Additional steps are necessary to strengthen the security of a new deployment before it is considered production ready. These may include:

- Disabling unnecessary features or plugins
- Restricting unnecessary connectivity (such as ports)
- Removing test databases
- Removing or renaming the default administrator or superuser accounts
- Configuring (and requiring) secure authentication
- Creating database users with limited permissions
- Modifying miscellaneous permissive settings

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Applied
