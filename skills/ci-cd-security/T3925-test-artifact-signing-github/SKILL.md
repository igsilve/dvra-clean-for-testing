---
name: t3925-test-artifact-signing-github
description: Verify that released artifacts are signed and that signatures are checked before deployment.
---

### Task T3925: Test artifact signing (GitHub) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T3925](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3925/)
**Priority:** 8

**Guidance:** Verification means taking a released artifact, confirming its signature validates against the expected identity, and confirming the deployment path rejects an unsigned artifact.

**Why Not Code-Fixable:**
- Searched: Repository root, .github/ (absent), Dockerfile
- Found: No release process or signed artifact exists.
- Missing: A release pipeline producing signed artifacts.
- Conclusion: The verification cannot be performed without a release process.

**Recommended Action:** The CI/CD owners should verify signing once a release process is in place.

**Status:** Documented
