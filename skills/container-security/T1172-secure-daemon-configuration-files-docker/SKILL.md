---
name: t1172-secure-daemon-configuration-files-docker
description: Secure daemon configuration files (Docker)
---

# T1172: Secure daemon configuration files (Docker)

**Category:** IN
**SD Elements:** [T1172](https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing/tasks/phase/deployment/4552-T1172/)
**Priority:** 8

### Task T1172: Secure daemon configuration files (Docker) (DOCUMENTATION ONLY)

**Guidance:** - Set docker.service file ownership to `root:root`.
- Set docker.service file permissions to `644` or more restrictive.

- Set docker.socket file ownership to `root:root`.
- Set docker.socket file permissions to `644` or more restrictive.

- Set /etc/docker directory ownership to `root:root`.
- Set /etc/docker directory permissions to `755` or more restrictive.

- Set registry certificate file ownership to `root:root`.

    Registry certificate files are usually found under /etc/docker/certs.d/<registry-name> directory.

- Set registry certificate file permissions to `444` or more restrictive.

- Set TLS CA certificate file ownership to `root:root`.

    TLS CA certificate file is the file that is passed alongwith`--tlscacert` parameter.

- Set TLS CA certificate file permissions to `444` or more restrictive.

- Set Docker server certificate file ownership to `root:root`.

    Docker server certificate file is the file that is passed alongwith`--tlscert` parameter.

- Set Docker server certificate file permissions to `444` or more restrictive.

- Set Docker server certificate key file ownership to `root:root`.

    Docker server certificate key file is the file that is passed alongwith`--tlskey` parameter.

- Set Docker server certificate key file permissions to `400`.

- Set Docker socket file ownership to `root:docker`.

    Docker daemon runs as 'root'. The default Unix socket hence must be owned by 'root'. Additionally, the Docker installer creates a Unix group called 'docker'. You can add users to this group, and then those users would be able to read and write to the default Docker Unix socket. The membership to the 'docker' group should be tightly controlled by the system administrator.

- Set Docker socket file permissions to `660` or more restrictive.

- Set daemon.json file ownership to `root:root`.
- Set daemon.json file permissions to `644` or more restrictive.

- Set /etc/default/docker file ownership to `root:root`.
- Set /etc/default/docker file permissions to `644` or more restrictive.

- Set /etc/sysconfig/docker file individual ownership and group ownership to `root`.
- Set /etc/sysconfig/docker file permissions to `644` or more restrictive.

**Why Not Code-Fixable:**
- Searched: application code, API services, deployment descriptors
- Found: no direct code path that can fully satisfy this requirement
- Missing: required external infrastructure or organizational controls
- Conclusion: this countermeasure requires documentation and process/infrastructure actions

**Recommended Action:** platform/security operations to implement and verify this control

**Status:** Documented
