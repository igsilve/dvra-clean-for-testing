---
name: no-shared-mount-propagation-docker
description: Use when code builds, accepts, or validates Docker or Docker Compose bind mounts and must reject shared or rshared mount propagation.
---
# Do not set mount propagation mode to `shared` (Docker)

## What This Skill Does
This skill removes unsafe Docker bind-mount propagation settings by rejecting any mount that uses `shared` or `rshared`. Use it when code generates Docker Compose service volumes, transforms user-provided mount settings, or validates resolved Compose configuration before deployment. The fix is to inspect every bind mount as structured data, allow only non-shared propagation values when present, and stop execution with a clear error if a service uses shared propagation.

## Decision Table
| Situation | Action |
|-----------|--------|
| Code builds or accepts Docker Compose bind mounts | Validate every service volume and inspect bind mount propagation before execution |
| A bind mount sets `bind.propagation` to `shared` or `rshared` | Reject configuration and return a clear validation error |
| Propagation is present and set to `private`, `rprivate`, `slave`, or `rslave` | Allow the configuration |
| Mounts are represented as free-form strings | Refactor to structured fields so type, source, target, and propagation can be validated |
| Configuration already omits propagation or uses only non-shared values | No action needed |

## Boundaries

### Can Do
- Add validation that rejects `shared` and `rshared` on Docker bind mounts
- Refactor mount handling from free-form strings to structured fields for safer inspection
- Validate all services and bind mounts in resolved Compose configuration before deployment

### Cannot Do
- Guarantee safety of non-bind volumes or unrelated Docker security settings
- Infer valid behavior from ambiguous short-form volume strings without parsing them first
- Replace broader container hardening such as user, capability, or privilege restrictions

## Gotchas
- Checking only one service or the first volume: unsafe propagation can appear in any service volume, so validation must inspect all bind mounts
- Treating missing propagation as a failure: omission is acceptable here; only `shared` and `rshared` must be rejected
- Matching only `shared` and forgetting `rshared`: both are unsafe and must be blocked

## Quick Verification
```bash
# Find explicit shared propagation in Compose files
grep -RInE 'propagation:[[:space:]]*(shared|rshared)\b' .

# Render the final Compose config and inspect all resolved volumes
docker compose config

# Example: fail verification if resolved config still contains shared propagation
docker compose config | grep -nE 'propagation:[[:space:]]*(shared|rshared)\b'
```