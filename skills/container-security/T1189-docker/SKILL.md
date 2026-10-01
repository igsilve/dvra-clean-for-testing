---
name: test-linux-security-modules-securely-configured-docker
description: Ensure Docker-managed containers run with non-empty Linux Security Module/AppArmor profiles and surface missing/invalid profiles as security failures; Use when code inspects or manages container security posture.
---

# Test if Linux Security Modules are securely configured (Docker)

## What This Skill Does
This skill helps agents detect and fix cases where Docker containers are run without a constrained Linux Security Module (LSM) profile (for example, AppArmor) or with empty/missing profiles. It guides changes so that container-management code inspects each container’s LSM/AppArmor profile, flags missing or empty profiles as security failures, and reports one clear, normalized profile result per container.

## Decision Table
| Situation | Action |
|-----------|--------|
| Application enumerates Docker containers but never reads `AppArmorProfile` or equivalent LSM field from inspection APIs | Add logic to inspect each container’s profile (e.g., `docker inspect .AppArmorProfile`) and include it in security checks |
| Inspection or reporting code accepts empty, missing, or `"unconfined"` AppArmor profiles as OK | Treat missing/empty/unconfined profiles as INVALID and fail the overall security check |
| Tool emits ad-hoc, ambiguous logs instead of a stable container-to-profile mapping | Normalize output to one structured record per container (ID → profile or INVALID marker) in machine-parseable form |
| Dockerfiles or docs instruct operators to run with `--security-opt apparmor=unconfined` or give no profile expectations | Remove/replace that guidance and document running with a non-empty profile (e.g., `--security-opt apparmor=docker-default`) |
| Code already fetches and validates non-empty LSM/AppArmor profiles and reports them per container | No action needed |

## Boundaries

### Can Do
- Identify when container security tooling fails to query or validate LSM/AppArmor profiles for each container.
- Recommend checks that treat missing, empty, or unconfined profiles as security failures and aggregate results safely.
- Suggest Docker run and documentation patterns that enforce non-empty AppArmor profiles (e.g., `apparmor=docker-default`).
- Encourage structured, deterministic output that maps each container ID to exactly one evaluated profile or an INVALID marker.

### Cannot Do
- Cannot enforce AppArmor/LSM profiles purely from inside a Dockerfile; actual enforcement happens at container run/host configuration.
- Cannot discover real-time host configuration, available AppArmor profiles, or Docker daemon settings.
- Cannot generate or maintain real AppArmor profile definitions; only reference their use and expected presence.
- Cannot guarantee that every environment uses AppArmor specifically (some may use other LSMs or none); logic must be defensive.

## Gotchas
- Treating `"unconfined"` or an empty `AppArmorProfile` as acceptable: This defeats confinement; code should treat these as INVALID and fail the security check.
- Only sampling a subset of containers: Tools that don’t enumerate all relevant containers can miss unconfined ones; always iterate over the full set your system manages.
- Free-form log text without structure: If outputs aren’t machine-parseable or don’t bind profiles to stable container identifiers, automated checks will be brittle and may miss insecure containers.

## Quick Verification
```bash
# 1) Start at least one container with a secure profile and one unconfined (for testing only)
docker run -d --rm --name secure-demo \
  --security-opt apparmor=docker-default \
  ubuntu:22.04 sleep infinity

docker run -d --rm --name insecure-demo \
  --security-opt apparmor=unconfined \
  ubuntu:22.04 sleep infinity

# 2) Inspect profiles and confirm tooling behavior
docker ps --quiet --all | xargs -n1 -I {} docker inspect \
  --format '{{ .Id }} {{ .Name }} AppArmorProfile={{ .AppArmorProfile }}' {}

# 3) Expected from the fixed logic:
# - Exactly one record per container ID
# - Non-empty profile for secure-demo
# - insecure-demo reported with an explicit INVALID marker or causes a failed security check
```