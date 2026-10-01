---
name: t2661-change-insecure-configuration-defaults-and-remove-unnecess
description: Change insecure database defaults and remove features the application does not use.
---

### Task T2661: Change insecure configuration defaults and remove unnecessary features (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2661](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2661/)
**Priority:** 9

**Guidance:** The server should be brought to a hardened baseline: default accounts removed, sample databases dropped, unused extensions and procedural languages disabled, and listen addresses narrowed.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/migrations/versions/, app/db/session.py
- Found: The stock PostgreSQL image runs with default settings, a default superuser named `admin` and a fixed password from the compose file.
- Missing: A hardened server configuration and the baseline that defines it.
- Conclusion: Server hardening is applied to the database instance, not through application source.

**Recommended Action:** The database administration team should apply the hardening baseline to the instance.

**Status:** Documented
