---
name: test-linux-kernel-capabilities-restricted-containers
description: Ensure Docker/containerized workloads do not run privileged and only use a minimal, policy-approved set of Linux kernel capabilities; use when reviewing container specs, Dockerfiles, or orchestrator configs for capability and privileged mode safety.
---

# Test if Linux Kernel Capabilities are restricted within containers (Docker)

## What This Skill Does
Checks and enforces that containers do not run in privileged mode and only have a strictly limited, policy-approved set of Linux kernel capabilities. It helps agents spot over-privileged containers (e.g., `--privileged`, `--cap-add=ALL`) and guides them to recommend capability-dropping and explicit policy checks in code, orchestrator manifests, and Docker usage.

## Decision Table
| Situation | Action |
|-----------|--------|
| Container run command or manifest uses `--privileged` or `privileged: true` | Recommend setting privileged mode to false (`--privileged=false` / `privileged: false`) and enforcing this via server-side policy or admission control. |
| Container spec uses `--cap-add=ALL` or a broad `CapAdd` without corresponding `CapDrop` | Recommend `--cap-drop=ALL` (or full drop list) then adding back only the minimal required capabilities; document allowed adds per container role. |
| Code passes user-controlled capability flags directly into Docker/OCI APIs | Introduce a strict, server-side policy mapping per container role and validate requested capabilities against this mapping before creating/starting containers. |
| Capability lists are missing, case-mismatched, or represented inconsistently (`cap_add`, `CapAdd`, `CAP_NET_ADMIN` vs `net_admin`) | Normalize capability names, treat missing lists as empty, and compare against policy case-insensitively to avoid bypasses. |
| Container already runs with `privileged: false`, `cap-drop=ALL`, and a minimal documented `cap-add` | No change to runtime flags; optionally add comments/docs or automated checks confirming these constraints. |

## Boundaries

### Can Do
- Identify and flag obviously over-privileged configurations in Dockerfiles, `docker run` examples, and Kubernetes/compose specs (e.g., `--privileged`, `--cap-add=ALL`, missing `cap-drop`).
- Suggest safer patterns: `--privileged=false`, `--cap-drop=ALL` plus minimal `--cap-add`, running as non-root, and documenting capability policies.
- Propose code-level and policy-level checks (e.g., validating capability sets and privileged flags in server-side logic or admission controllers).

### Cannot Do
- Cannot inspect or verify real runtime container states, host kernel settings, or orchestrator admission policies beyond what is shown in the code/config.
- Cannot derive the exact minimal capability set a workload truly needs from arbitrary business logic; can only recommend least-privilege patterns and examples.
- Cannot generate or maintain organization-wide policy mappings for all container roles; those must be defined by humans and enforced by your CI/CD or platform.

## Gotchas
- Assuming default capabilities are “safe enough”: Default Docker capabilities are still powerful; without `cap-drop=ALL` plus explicit minimal `cap-add`, containers may retain unnecessary kernel powers.
- Treating missing capability arrays as “don’t care”: If absent lists are not treated as empty sets in validation logic, attackers can bypass checks by omitting fields entirely.
- Relying only on client-side flags or comments: If policy enforcement lives only in `docker run` examples or documentation and not in server-side checks or admission controllers, users can still launch over-privileged containers.

## Quick Verification
```bash
# List capabilities and privileged status for all running containers (Docker CLI)
docker ps -q | xargs -r docker inspect \
  --format '{{.Name}} privileged={{.HostConfig.Privileged}} CapAdd={{.HostConfig.CapAdd}} CapDrop={{.HostConfig.CapDrop}}'

# Check a specific container is not privileged and uses minimal caps
CID="<container-id-or-name>"
docker inspect "$CID" \
  --format 'Name={{.Name}} privileged={{.HostConfig.Privileged}} CapAdd={{.HostConfig.CapAdd}} CapDrop={{.HostConfig.CapDrop}}'

# Show Kubernetes pod security context and container capabilities
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].name}{"\n"}{.spec.containers[*].securityContext}{"\n"}'

# Attack test: attempt to run privileged and confirm policy rejects/blocks it
docker run --rm --privileged --cap-add=ALL your-image || echo "Blocked as expected"
```