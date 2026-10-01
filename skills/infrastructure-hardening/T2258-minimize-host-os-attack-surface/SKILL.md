---
name: t2258-minimize-host-os-attack-surface
description: Minimize the attack surface of the hosts running this service.
---

### Task T2258: Minimize host OS attack surface (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T2258](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T2258/)
**Priority:** 7

**Guidance:** Container hosts should run a minimal operating system with unused services disabled, unnecessary packages removed, local firewalling enabled and remote access limited to a bastion path.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: The repository defines the container image but nothing about the host operating system it runs on.
- Missing: Host build configuration and a hardening baseline.
- Conclusion: Host hardening is applied to the machine image, outside this repository. The equivalent work inside the container image is tracked separately under the image attack-surface countermeasure.

**Recommended Action:** The platform team should apply the host hardening baseline to the container hosts.

**Status:** Documented
