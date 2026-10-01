---
name: t2665-protect-sensitive-data-at-rest-with-encryption
description: Encrypt sensitive data at rest across the systems that hold it.
---

### Task T2665: Protect sensitive data at rest with encryption (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2665](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2665/)
**Priority:** 8

**Guidance:** Data classified as sensitive should be encrypted wherever it resides — database files, backups, log archives and object storage — with keys managed centrally and rotated.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/models.py, app/config.py
- Found: The database volume, any log output and any backup copy are all unencrypted.
- Missing: Storage encryption across each of those layers plus a key management service.
- Conclusion: Encryption at rest spans storage platforms and key management, which are infrastructure concerns.

**Recommended Action:** The platform team should apply encryption at rest to every store holding this service's data.

**Status:** Documented
