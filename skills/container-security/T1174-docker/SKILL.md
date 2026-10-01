---
name: create-non-root-users-for-containers-docker
description: Use when a Dockerfile runs the final container as root or does not define a dedicated runtime user; creates and enforces a non-root runtime user for the final image stage.
---

# Create non-root users for containers (Docker)

## What This Skill Does
This skill fixes Docker images that run as root by default. It updates the Dockerfile to create a dedicated non-root runtime user, ensure privileged setup happens before switching users, assign correct ownership or permissions to application files and writable paths, and keep the final effective `USER` in the runtime stage non-root. This reduces the impact of a compromise by removing unnecessary root privileges from the running container.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile has no `USER` instruction in the final runtime stage | Create a dedicated non-root user and set `USER` to that account in the final runtime stage |
| Final effective user is `root` or the Dockerfile switches back to `root` later | Move privileged setup earlier and ensure the last effective `USER` remains the non-root account |
| Application files are copied without ownership suitable for the runtime user | Use `COPY --chown=user:group` where supported, or `chown` required paths before switching users |
| Multi-stage build uses a secure builder stage but final stage still runs as root | Apply the non-root user fix in the final runtime stage, not just the builder stage |
| Dockerfile already creates a dedicated runtime user, sets correct ownership, and ends on non-root | No action needed |

## Boundaries

### Can Do
- Add a dedicated non-root user and group in a Dockerfile
- Reorder Dockerfile steps so privileged setup happens before `USER`
- Adjust ownership and permissions for app directories and required writable paths

### Cannot Do
- Guarantee the application itself is compatible with reduced privileges
- Infer every runtime write location without inspecting app behavior
- Replace orchestrator-level controls such as Kubernetes `securityContext` or Docker runtime flags

## Gotchas
- Setting `USER` too early: later `RUN` steps may fail or tempt a switch back to root in the final stage
- Forgetting file ownership updates: the container may start as non-root but fail reading config, writing logs, or creating temp files
- Fixing only the builder stage: the final image can still run as root if the runtime stage does not set a non-root `USER`

## Quick Verification
```bash
# Build the image
docker build -t app-nonroot .

# Confirm the container runs as a non-root UID
docker run --rm app-nonroot id -u

# Confirm the effective user is not root
docker run --rm app-nonroot sh -c 'id && whoami || true'

# Check the app directory ownership and permissions
docker run --rm app-nonroot sh -c 'ls -ld /app && ls -l /app | head'

# Negative check: writing to a root-owned restricted path should fail
docker run --rm app-nonroot sh -c 'touch /root/should-fail'
```