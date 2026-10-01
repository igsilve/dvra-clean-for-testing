---
name: do-not-share-host-network-namespace-docker
description: Use when Docker or Compose service configuration may set network_mode to host; validate resolved config and reject explicit host network namespace sharing.
---
# Do not share the host's network namespace (Docker)

## What This Skill Does
This skill prevents containers from joining the host network namespace by detecting and rejecting any resolved Docker or Docker Compose service configuration that explicitly sets `network_mode: host`. It should be applied where code generates, merges, mutates, parses, or validates container configuration before deployment. The fix is to validate the fully resolved configuration, fail closed on parse or resolution errors, and allow services that simply omit `network_mode`.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Docker Compose service resolves to `network_mode: host` | Reject the configuration and require removal of host networking |
| Configuration is built from multiple files, templates, or overrides | Validate the fully resolved configuration after merges, not just source fragments |
| Parsing, interpolation, or resolution fails | Fail closed and reject deployment or generation |
| A service omits `network_mode` entirely | No action needed |
| Code directly emits or mutates Compose YAML with `network_mode: host` | Remove that setting and keep the service on Docker-managed networking |

## Boundaries

### Can Do
- Detect and block explicit `network_mode: host` in resolved Docker Compose service definitions
- Update generators or validators to inspect merged or overridden service configuration
- Preserve compliant services that do not set any `network_mode`

### Cannot Do
- Guarantee runtime isolation if deployment happens outside the validated configuration path
- Infer intent from broken or partial configuration; invalid input must be rejected
- Fix unrelated Docker hardening issues such as privileged mode, broad port exposure, or dangerous volume mounts

## Gotchas
- Checking only raw source files: this is wrong because overrides, anchors, env substitution, or generated config may still resolve to `network_mode: host`
- Rejecting missing `network_mode`: this is wrong because only explicit host mode is non-compliant; omission is allowed
- Auto-rewriting invalid config to "something safe": this is wrong because unevaluable or malformed input should fail closed, not be guessed

## Quick Verification
```bash
# Show the fully resolved Compose configuration
docker compose -f docker-compose.yml config

# Confirm no service resolves to host networking
docker compose -f docker-compose.yml config | grep -n "network_mode: host" && echo "FAIL" || echo "PASS"

# Negative test: a file with host networking should be rejected by the application validator
docker compose -f vulnerable-compose.yml config

# Positive test: a compliant file without host networking should resolve cleanly
docker compose -f mitigated-compose.yml config
```