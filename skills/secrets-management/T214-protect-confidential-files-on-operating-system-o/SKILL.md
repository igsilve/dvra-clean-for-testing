---
name: t214-protect-confidential-files-on-operating-system-or-server
description: Protect confidential files on the operating system and server hosting this service.
---

### Task T214: Protect confidential files on operating system or server (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T214](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T214/)
**Priority:** 9

**Guidance:** Files holding credentials, keys or sensitive data should be owned by the service account, unreadable by other users, stored on encrypted media, and excluded from images and backups that travel more widely.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, app/config.py, start_app.sh
- Found: Configuration is loaded from a `.env` file resolved relative to the working directory and the compose file carries credentials inline, but the repository sets no ownership or mode on any of it.
- Missing: Host filesystem permissions, a secret mount arrangement and encrypted storage for the host.
- Conclusion: File protection is applied on the host and through the secret delivery mechanism, not through application source. The related code change — removing in-code secret defaults — is tracked separately.

**Recommended Action:** The platform team should deliver secrets through restricted-permission secret mounts on encrypted storage.

**Status:** Documented
