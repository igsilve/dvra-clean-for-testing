---
name: t2665-protect-sensitive-data-at-rest-with-encr
description: Protect sensitive data at rest with encryption
---

# T2665: Protect sensitive data at rest with encryption

**Category:** IN
**SD Elements:** [T2665](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T2665/)
**Priority:** 8

### Task T2665: Protect sensitive data at rest with encryption (DOCUMENTATION ONLY)

**Guidance:** Database servers should use file system encryption, which is performed at the operating system level. Examples include FDE (Full Disk Encryption) in Linux or BitLocker in Windows. 

Additionally:
- If your database provides integrated at-rest data encryption (such as TDE, or Transparent Data Encryption), this feature should be enabled.
- If your database does not provide integrated at-rest encryption, review your organization's security policy and compliance requirements to determine if file system encryption is sufficient. A development-time mitigation is to use application-side encryption on specific fields, but this increases complexity and can cause vulnerabilities related to key management. Other options include using trusted database extensions or platform services that can provide at-rest database encryption.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
