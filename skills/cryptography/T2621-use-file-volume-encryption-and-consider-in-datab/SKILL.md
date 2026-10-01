---
name: t2621-use-file-volume-encryption-and-consider-in-database-encryp
description: Encrypt the database file volume and consider in-database encryption for the most sensitive columns.
---

### Task T2621: Use file volume encryption and consider in-database encryption with pgcrypto (PostgreSQL) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2621](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2621/)
**Priority:** 8

**Guidance:** The volume holding database files should be encrypted at the storage layer, with pgcrypto used selectively for columns that must stay unreadable even to someone with file access.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/db/models.py, app/migrations/versions/
- Found: The `pg_volume` Docker volume is unencrypted and no pgcrypto extension is enabled in the migrations.
- Missing: Storage-layer encryption for the volume and a key management arrangement.
- Conclusion: Volume encryption is a storage platform capability configured outside this repository.

**Recommended Action:** The platform and database administration teams should encrypt the database volume and select columns for pgcrypto.

**Status:** Documented
