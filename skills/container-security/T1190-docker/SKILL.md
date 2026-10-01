---
name: restrict-linux-kernel-capabilities-within-containers-docker
description: Restrict Linux capabilities and forbid privileged containers in Docker-based apps; Use when code starts or configures containers and may grant excessive kernel privileges
---

# Restrict Linux Kernel Capabilities within containers (Docker)

## What This Skill Does
Enforces least-privilege Linux kernel capabilities for containers and forbids privileged containers in Docker-based systems. It focuses on application/orchestration code and Dockerfiles that encourage or rely on `--privileged` or extra capabilities, replacing them with patterns that assume default/reduced capabilities and validate configuration before reaching the container runtime.

## Decision Table
| Situation | Action |
|-----------|--------|
| Container is documented or expected to run with `--privileged` or full capabilities | Remove privileged requirement, document non-privileged usage, and ensure image runs correctly with default/reduced capabilities (e.g., non-root user, minimal packages) |
| Application/orchestrator code passes `privileged=true` or extra capabilities (e.g., `cap_add`) to Docker or a container runtime client | Introduce a validator that rejects privileged mode and non-default capabilities; call it in all code paths that start containers |
| There are multiple components/services that can start containers directly (each calling Docker or Kubernetes APIs) | Introduce a central "runner" abstraction/service that applies capability and privileged policy, and route all container-starting calls through it |
| API endpoints accept user/container specs that include capabilities or privileged flags | Add input validation that normalizes and checks capabilities against an allowed set and rejects privileged requests before invoking any runtime client |
| Code or configuration only uses Docker defaults, never sets `--privileged`, and does not add extra capabilities | No action needed beyond optional documentation and tests confirming privileged/extra-capability attempts are rejected |

## Boundaries

### Can Do
- Detect and refactor Dockerfiles that implicitly or explicitly rely on `--privileged` or broad capabilities.
- Add or improve application-level validation for `privileged` flags and capability lists before calling container runtimes.
- Introduce or tighten a central runner abstraction that consistently enforces capability and privileged policies across services.

### Cannot Do
- Modify host-level kernel, Docker daemon, or Kubernetes cluster policies (e.g., PodSecurityPolicy, seccomp, AppArmor) beyond application and image code.
- Guarantee that operators or external systems won't manually start containers with `--privileged` or extra capabilities outside the application's control.
- Accurately list "Docker default" capabilities for a specific runtime version or distro; humans must confirm exact default sets for their environment.

## Gotchas
- Assuming dropping capabilities is unsafe: dropping capabilities (even ones not present by default) is always safe and should never be blocked; only adding capabilities or enabling privileged mode must be rejected.
- Enforcing policy in some code paths only: if any path creates containers without going through the validator/runner abstraction, attackers can bypass restrictions; ensure all container-starting calls share the same enforcement layer.
- Relying solely on comments or docs (e.g., "do not run with `--privileged`") without runtime checks: comments do not prevent misconfiguration; add validators, entrypoints, or integration tests that fail when privileged or extra capabilities are used.

## Quick Verification
```bash
# 1) Verify Dockerfile runs correctly without --privileged and with reduced caps
docker build -t secure-cap-container .
docker run --rm \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  secure-cap-container

# 2) Confirm privileged container is rejected by orchestration/app code
# (Replace URL and payload with your API/runner interface)
curl -sS -X POST http://127.0.0.1:8080/run-container \
  -H "Content-Type: application/json" \
  -d '{"image":"ubuntu:22.04","privileged":true}' \
  -o /dev/null -w "%{http_code}\n"

# Expect: non-2xx status and a clear error about privileged containers being forbidden.

# 3) Confirm non-default capability is rejected by policy
curl -sS -X POST http://127.0.0.1:8080/run-container \
  -H "Content-Type: application/json" \
  -d '{"image":"ubuntu:22.04","cap_add":["SYS_ADMIN"]}' \
  -o /dev/null -w "%{http_code}\n"

# Expect: non-2xx status and a clear error about unsupported capabilities.
```