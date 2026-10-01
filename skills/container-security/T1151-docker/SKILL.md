---
name: verify-container-networks-docker
description: Verify Docker daemon network flags and port bindings to avoid improper container network configuration; use when containers or Dockerfiles may expose services too broadly
---

# Verify that container networks are configured properly (Docker)

## What This Skill Does
This skill helps tighten Docker network configuration so containers are not exposed more broadly than intended. It focuses on verifying and guiding fixes around Docker daemon flags (`--icc`, `--iptables`, `--userland-proxy`) and host port bindings (avoiding `0.0.0.0`). It is mainly for code and Dockerfile changes that document, assert, or validate these policies rather than trying to enforce host daemon settings from inside a container.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile or entrypoint script tries to parse/validate Docker daemon flags | Centralize the parsing and validation logic; strictly enforce `--icc=false`, `--userland-proxy=false`, and absence of `--iptables=false` as the allowed policy |
| Application or tooling code builds or validates Docker daemon configs (JSON or CLI flags) | Add strict boolean validation: require `icc=false`, `userland-proxy=false`, and treat `iptables=false` as non-compliant; reject malformed or ambiguous values |
| Code constructs `docker run` / compose / Kubernetes port bindings without host IP restriction (defaulting to `0.0.0.0`) | Update to require explicit, allowed host IPs (e.g., `127.0.0.1:8080:80`); reject or rewrite `0.0.0.0` or empty host IP bindings |
| Dockerfile for sensitive/admin services includes `EXPOSE` on common HTTP/management ports | Remove or narrow `EXPOSE`; add labels or docs that require binding only to specific host interfaces and hardened daemon flags |
| Code/image only documents network policy and does not touch daemon or bindings | If policy is already clearly documented and does not encourage `0.0.0.0` or weak flags, take no action |

## Boundaries

### Can Do
- Add or adjust **validation logic** in apps, tooling, or entrypoint scripts that inspect Docker daemon flags or config files to:
  - Enforce `--icc=false`
  - Enforce `--userland-proxy=false`
  - Forbid `--iptables=false`
- Update **Dockerfiles** to:
  - Avoid unsafe `EXPOSE` usage for sensitive/admin services
  - Add labels and comments documenting required network policies and safe `docker run` examples (e.g., non-wildcard host IPs)
- Harden **code that generates or approves** container run requests or orchestrator manifests (compose, Kubernetes, custom systems) by:
  - Rejecting `0.0.0.0` / wildcard bindings
  - Allowing only explicit, approved host interface IPs or ranges

### Cannot Do
- Cannot reliably **reconfigure the host Docker daemon** (e.g., change `/etc/docker/daemon.json` or `dockerd` flags) from inside application code or Dockerfiles.
- Cannot guarantee **runtime deployment policies** (cluster-level network policies, host firewall rules, orchestrator defaults); these require external ops changes.
- Cannot infer or enforce **real network topology or IP allowlists** without project-specific rules; can only recommend patterns and clear validation points.

## Gotchas
- Treating `icc`, `iptables`, or `userland-proxy` values as loose strings: relying on substring/partial matches (e.g., accepting `"False"`, `"0"`, `"off"`) can misclassify settings. Use strict boolean parsing and canonical values (`true`/`false`) only.
- Assuming Dockerfile changes can enforce host daemon flags: comments, labels, and entrypoint checks can **detect** non-compliance but do not actually start `dockerd` with secure options; deployment still must configure the daemon properly.
- Allowing implicit `0.0.0.0` bindings: many tools default to wildcard host IP when the IP is omitted. Validation must treat missing host IP as unsafe unless your policy explicitly allows it and rewrites it to a safe address.

## Quick Verification
```bash
# 1) Verify dockerd flags on the host
ps aux | grep '[d]ockerd'

# Confirm:
# - --icc=false is present (or icc": false in daemon.json)
# - --userland-proxy=false is present (or "userland-proxy": false)
# - --iptables=false is NOT present (iptables is true or omitted)

# 2) Check that published ports are not bound to 0.0.0.0
docker ps --format '{{.Ports}}'

# Look for entries like:
# 0.0.0.0:8080->80/tcp  # NON-COMPLIANT
# 127.0.0.1:8080->80/tcp # COMPLIANT (example if localhost is allowed)

# 3) For a given image, inspect Dockerfile metadata
docker image inspect <image> --format '{{json .Config.ExposedPorts}} {{json .Config.Labels}}' | jq

# Confirm:
# - Sensitive/admin images avoid broad EXPOSE on common ports, or have clear labels
# - Labels/documentation reflect hardened network policy (no 0.0.0.0 bindings)

# 4) If an entrypoint guard is added, attempt to run under non-compliant daemon
docker run --rm <image>  # Should fail fast with a clear error when flags/policies are violated
```