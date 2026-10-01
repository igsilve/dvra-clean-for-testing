---
name: restrict-containers-from-acquiring-additional-privileges-docker
description: Use when Docker Compose or similar container service definitions allow missing or inconsistent no-new-privileges protection and need explicit service-level restriction.
---

# Restrict containers from acquiring additional privileges (Docker)

## What This Skill Does
This skill fixes Docker and Docker Compose service configurations that allow containers to gain additional privileges at runtime. It does this by adding an explicit service-level `security_opt` entry with `no-new-privileges:true` to every in-scope service, so processes inside the container cannot elevate privileges through setuid, setgid, or similar paths. It also flags obviously risky settings like `privileged: true` or broad capability grants that weaken the intended container boundary.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Docker Compose service lacks `security_opt` or does not include `no-new-privileges:true` | Apply the fix by adding `security_opt: [no-new-privileges:true]` at that service |
| A project has multiple services and only some define `no-new-privileges:true` | Add the setting explicitly to each in-scope service; do not rely on another service's config |
| A service uses `privileged: true` or `cap_add: [ALL]` | Add `no-new-privileges:true` and reduce privileges where safe, such as removing `privileged` or replacing broad adds with `cap_drop` |
| The service already defines `security_opt` with exact `no-new-privileges:true` | No action needed |
| The configuration is not a Docker service definition | Do not apply this skill; use a platform-specific hardening approach instead |

## Boundaries

### Can Do
- Add explicit `security_opt` entries with `no-new-privileges:true` to Docker Compose services
- Update each in-scope service individually so the restriction is not only implied elsewhere
- Point out nearby privilege risks such as `privileged: true` and excessive capability grants

### Cannot Do
- Guarantee the application will still work if it depended on privilege escalation behavior
- Prove runtime enforcement without checking the effective rendered or running container configuration
- Secure non-Docker platforms such as Kubernetes, Podman, or raw host service managers with Docker-specific syntax

## Gotchas
- Adding the setting only to one service: each in-scope service must declare it explicitly or it may remain unprotected
- Using an inexact value or wrong key: the restriction must be `security_opt` with exact `no-new-privileges:true` or the runtime may not preserve it
- Leaving `privileged: true` in place and assuming this fix is enough: `no-new-privileges` helps, but broad privilege settings still expand attack impact

## Quick Verification
```bash
# Render the effective Compose configuration and confirm each service includes no-new-privileges:true
docker compose config

# Inspect a running container and check the security options applied
docker inspect <container_name_or_id> --format '{{json .HostConfig.SecurityOpt}}'

# List containers started by Compose, then inspect the target service container
docker compose ps
```