---
name: configure-container-networks-properly-docker
description: Secure Docker container networking by constraining exposure, binding to specific interfaces, and validating peers. Use when services may be reachable from unintended containers or host interfaces.
---

# Configure container networks properly (Docker)

## What This Skill Does
Helps reconfigure Docker container networking so services are not unintentionally exposed to other containers or host interfaces. It focuses on restricting inter-container traffic, validating and documenting allowed peers, binding services to explicit addresses and ports, avoiding reliance on Docker’s userland proxy, and using health checks to detect network misconfiguration, all without changing Docker daemon flags directly from code.

## Decision Table
| Situation | Action |
|-----------|--------|
| Service listens on `0.0.0.0` inside the container and is meant to be internal-only | Change app/config to bind to `127.0.0.1` (or a specific interface) and expose only the needed port; avoid broad `EXPOSE` hints if not required |
| Any container on the default bridge network can reach a sensitive service | Use labels and/or config to declare an allow-list of peer services, attach the container only to restricted user-defined networks, and avoid implicit exposure via `EXPOSE` + broad `-p` mappings |
| App depends on outbound network access and “just hangs” when misconfigured | Add explicit health checks (Docker `HEALTHCHECK` and/or in-app preflight) to verify outbound reachability and fail fast with clear but non-sensitive diagnostics |
| Deployment relies on Docker’s userland proxy or implicit port publishing behavior | Make binding behavior explicit in app (bind to known address/port), document expectation via `ENV` or comments, and recommend running with `--userland-proxy=false` plus explicit port mappings |
| Code already binds to a validated address and uses an allow-list of peers with clear logging | No action needed; keep configuration and documentation up to date and avoid reintroducing broad bindings or unvalidated peers |

## Boundaries

### Can Do
- Adjust Dockerfiles to: use `EXPOSE` conservatively, add labels, define `HEALTHCHECK`, and set safe default bind-related environment variables.
- Propose and sketch application-level patterns (allow-list of peers, startup preflight checks, safe default bind addresses, logging of effective bind address/port).
- Recommend runtime flags and orchestrator policies in comments or documentation (e.g., user-defined networks, `-p 127.0.0.1:8080:8080`, disabling userland proxy).

### Cannot Do
- Directly modify Docker daemon or orchestrator configuration files (e.g., cannot actually set `--userland-proxy=false` or iptables rules; can only document them).
- Guarantee real network isolation or policy enforcement; that depends on the runtime environment (Swarm, Kubernetes, host firewall, etc.).
- Look up actual IP addresses, hostnames, or live network state to verify connectivity; only static code and config can be inspected.

## Gotchas
- Assuming `EXPOSE 8080` is “just documentation”: Docker and tools treat `EXPOSE` as a hint; combined with defaults and `docker run -P`, it can still broaden exposure. Use it only when you really intend that port to be reachable.
- Binding to `0.0.0.0` “for convenience”: inside a container this means “accept from anywhere on attached networks.” This is unsafe for services that should be reachable only from specific peers or host interfaces; prefer `127.0.0.1` or a specific interface with explicit port mappings.
- Overloading health checks with sensitive details: health-check scripts or endpoints that print full URLs, credentials, or internal topology can leak information. Health checks should distinguish app vs. network failures without exposing secrets or detailed network maps.

## Quick Verification
```bash
# 1. Confirm what address the app is actually listening on inside the container
docker run --rm --net bridge --name test-net -p 8080:8080 my-image \
  sh -c "ss -tuln | grep 8080 || netstat -tuln | grep 8080"

# 2. Test from another container on the same network (should FAIL for properly isolated internal-only services)
docker network create test-net
docker run -d --name svc --network test-net my-image
docker run --rm --network test-net curlimages/curl curl -sS http://svc:8080/ || echo "unreachable (expected for isolated service)"

# 3. Verify host interface binding (only localhost)
docker run -d --name bind-test -p 127.0.0.1:8080:8080 my-image
curl -sS http://127.0.0.1:8080/ || echo "no response on localhost"
# Try from another host or interface; connection should fail.

# 4. Check Docker health status for outbound connectivity issues
docker inspect --format='{{.State.Health.Status}}' svc || echo "no healthcheck defined"
```