---
name: set-container-cpu-priority-docker
description: Use when Docker or Compose container definitions lack explicit CPU shares or CPU consumption controls and need fair scheduling or hard CPU limits.
---
# Set container CPU priority (Docker)

## What This Skill Does
This skill fixes Docker container configurations that omit explicit CPU scheduling weight or CPU allocation controls. It adds `cpu_shares` when services need relative CPU priority under contention, or `cpus` when a service must not exceed a defined CPU amount. It also helps validate that configured values are present, numeric, and positive so containers cannot run with accidental unlimited CPU access.

## Decision Table
| Situation | Action |
|-----------|--------|
| Docker Compose service has no `cpu_shares`, `cpus`, or equivalent CPU control | Apply explicit CPU control based on service needs |
| Service needs relative priority over other containers during CPU contention | Add positive `cpu_shares` and use higher values for higher-priority services |
| Service must not exceed a defined CPU amount | Add positive `cpus` value as a hard CPU allocation |
| Generated or templated container config may contain missing, non-numeric, or non-positive CPU values | Add validation and reject invalid configuration |
| Service already has explicit, valid CPU controls appropriate for its runtime | No action needed |

## Boundaries

### Can Do
- Add `cpu_shares` for relative CPU priority in Docker Compose or similar Docker configuration
- Add `cpus` limits to prevent a container from consuming unlimited host CPU
- Flag missing, invalid, or non-positive CPU control values for validation

### Cannot Do
- Guarantee CPU reservation behavior on runtimes that do not support or enforce the chosen setting
- Infer the correct business priority of services without context from the application
- Replace broader resource isolation needs such as memory, PID, I/O, or orchestration-level policy

## Gotchas
- Using `cpu_shares` as if it were a hard limit: `cpu_shares` is only a relative weight during contention, not a maximum CPU cap
- Setting only one service's priority and leaving peers unconfigured: relative weighting is clearer and safer when comparable services all have intentional values
- Using zero, negative, or non-numeric CPU values: invalid values can be ignored, rejected, or lead to unintended unlimited CPU usage

## Quick Verification
```bash
# Validate the Compose file
docker compose config

# Start the services
docker compose up -d

# Observe CPU usage under load
docker stats

# Inspect rendered container settings
docker inspect <container_name> | grep -E 'CpuShares|NanoCpus'

# Optional: generate CPU contention and re-check relative behavior
docker exec -it <worker_container> sh -c 'python -c "while True: pass"'
```