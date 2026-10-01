---
name: t3908-enforce-artifact-signing-github
description: Sign the artifacts this project produces and require signatures downstream.
---

### Task T3908: Enforce artifact signing (GitHub) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T3908](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T3908/)
**Priority:** 8

**Guidance:** Every released artifact should be signed during the build, with signatures recorded in a transparency log, and consumers should verify the signature and provenance before deploying.

**Why Not Code-Fixable:**
- Searched: Repository root, .github/ (absent), Dockerfile, pyproject.toml
- Found: There is no release or publishing process in the repository; images are built and run locally.
- Missing: A release pipeline, a signing identity and key custody arrangements.
- Conclusion: Artifact signing requires a release pipeline and key management that do not exist for this project.

**Recommended Action:** The CI/CD owners should introduce signing as part of establishing a release process.

**Status:** Documented
