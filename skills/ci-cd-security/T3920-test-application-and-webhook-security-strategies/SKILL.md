---
name: t3920-test-application-and-webhook-security-strategies-github
description: Verify the application and webhook security controls on this repository.
---

### Task T3920: Test application and webhook security strategies (GitHub) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T3920](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3920/)
**Priority:** 8

**Guidance:** Verification means reviewing the installed application list against the approved set, confirming each grant is least privilege, and confirming every webhook uses a secret and HTTPS with signature verification at the receiver.

**Why Not Code-Fixable:**
- Searched: Repository root, .github/ (absent)
- Found: No webhook receivers or application manifests exist in the repository.
- Missing: Access to the hosting platform's settings, where installations and webhooks are configured.
- Conclusion: The evidence for this verification lives in platform settings rather than repository content.

**Recommended Action:** The repository administrators should perform the review in the platform settings and record the outcome.

**Status:** Documented
