---
name: t2601-use-transparent-data-encryption-with-enterprise-databases
description: Enable transparent data encryption on the database.
---

### Task T2601: Use Transparent Data Encryption with Enterprise Databases (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2601](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2601/)
**Priority:** 8

**Guidance:** The database should encrypt its data files at rest using keys held in a managed key store, with rotation and separation between the key custodian and the database administrator.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/session.py, app/config.py
- Found: PostgreSQL runs from the stock image with a plain volume; no encryption-at-rest configuration is present.
- Missing: Database server configuration, a key management service and the storage layer the volume lives on.
- Conclusion: Transparent data encryption is configured on the database server and storage platform, not in application source.

**Recommended Action:** The database administration team should enable encryption at rest with managed keys.

**Status:** Documented
