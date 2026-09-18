---
name: limit-resources-used-by-containers-docker
description: Use when Docker Compose services lack explicit memory and PID limits; adds finite per-service caps to prevent default unlimited container resource usage.
---

# Limit resources used by containers (Docker)

## What This Skill Does
This skill fixes Docker Compose configurations where services run without explicit resource limits, which can allow a container to consume unbounded memory or spawn excessive processes. It adds finite per-service memory caps and PID caps in the Compose file so workloads remain constrained and one container is less able to disrupt the host or neighboring services.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Compose service has no `mem_limit` and no `pids_limit` | Add both with finite per-service values |
| A Compose service has `mem_limit` but no `pids_limit` | Keep the memory cap and add a finite `pids_limit` |
| A Compose service has `pids_limit` but no `mem_limit` | Keep the PID cap and add a finite `mem_limit` |
| A Compose service uses non-finite or effectively unlimited values | Replace them with concrete finite values sized for expected workload |
| A service already has finite `mem_limit` and finite `pids_limit` | No action needed |

## Boundaries

### Can Do
- Add finite `mem_limit` values to applicable Compose services
- Add finite numeric `pids_limit` values to applicable Compose services
- Preserve existing service behavior while rendering the final Compose config for verification

### Cannot Do
- Determine the exact safe limit for every workload without app-specific knowledge
- Guarantee runtime stability if limits are set too low
- Fix resource controls outside Docker Compose, such as Kubernetes manifests or host-level cgroup settings

## Gotchas
- Setting only one limit: adding just memory or just PID limits still leaves one resource class effectively unbounded
- Using unrealistic caps: values that are too small can break startup or normal runtime behavior
- Trusting raw source only: Compose files can merge overrides, so verify the rendered result with `docker compose config`

## Quick Verification
```bash
# Render the final Compose configuration
docker compose config

# Inspect rendered limits for each service
docker compose config | grep -E "mem_limit|pids_limit"

# Start the stack and inspect runtime limits for a container
docker compose up -d
docker inspect <container_name_or_id> --format '{{.HostConfig.Memory}} {{.HostConfig.PidsLimit}}'
```