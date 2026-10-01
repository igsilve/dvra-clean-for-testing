---
name: t1155-verify-that-docker-registries-are-secure-docker
description: Verify that the container registries this project uses are reachable only over TLS with validated trust.
---

### Task T1155: Verify that Docker registries are secure (Docker) (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T1155](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T1155/)
**Priority:** 8

**Guidance:** Verification means confirming no insecure-registry setting is present on any daemon that builds or runs these images, that registry endpoints are HTTPS, and that the registry CA is installed on the host.

**Why Not Code-Fixable:**
- Searched: Dockerfile, docker-compose.yml, start_app.sh
- Found: Images come from Docker Hub by implicit reference; the daemon configuration that governs registry trust is not part of the repository.
- Missing: Access to the Docker daemon configuration on the build and runtime hosts.
- Conclusion: Registry trust is configured on the Docker daemon and host, outside any file in this repository.

**Recommended Action:** The platform team should verify daemon registry settings on the build and runtime hosts.

**Status:** Documented
