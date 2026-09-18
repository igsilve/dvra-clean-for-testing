---
name: mount-container-root-filesystem-read-only-docker
description: Use when Docker Compose services leave the container root filesystem writable; applies read_only and scopes writes to explicit tmpfs or narrow volumes.
---

# Mount container's root file system as read-only (Docker)

## What This Skill Does
This skill hardens Docker Compose services against P1091 by making the container root filesystem read-only and allowing writes only through explicitly approved paths. It applies `read_only: true` at the service level, then adds narrowly scoped `tmpfs` mounts for temporary runtime files or dedicated volumes for required persistent data so the application cannot write broadly across the image-backed filesystem.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Compose service has no `read_only: true` and does not need general filesystem writes | Add `read_only: true` to the service |
| The application needs temporary writes for `/tmp`, PID files, or cache directories | Keep `read_only: true` and add narrow `tmpfs` mounts only for those paths |
| The application needs persistent writes | Keep `read_only: true` and add a dedicated volume only for the exact data path that must be writable |
| A volume mounts a broad application path such as `/app` only to make writes work | Replace it with a narrower writable path such as `/app/data` and reconfigure the app to write there |
| The service already uses `read_only: true` and writes only to approved mounts | No action needed |

## Boundaries

### Can Do
- Add `read_only: true` to Docker Compose services
- Add scoped `tmpfs` mounts for ephemeral writable paths like `/tmp`
- Replace broad writable mounts with dedicated volumes for exact approved data paths

### Cannot Do
- Guarantee the application will work without identifying all runtime write paths first
- Automatically rewrite application code or framework settings that still write to blocked locations
- Secure Kubernetes, Docker CLI flags, or non-Compose container definitions unless they are explicitly in scope

## Gotchas
- Adding `read_only: true` without writable exceptions: the app may fail if it writes to `/tmp`, runtime directories, or cache locations
- Mounting a broad writable path like `/app`: this weakens the control by letting the app modify more of its filesystem than necessary
- Assuming logs should be written to local files: many containers should log to stdout/stderr instead of opening writable filesystem paths

## Quick Verification
```bash
# Check that Compose services now declare read_only
grep -n "read_only: true" docker-compose.yml compose.yml 2>/dev/null

# Start the service
docker compose up -d

# Confirm writes to the root filesystem fail
docker compose exec app sh -lc 'echo test > /etc/test-file' || true

# Confirm writes to the approved writable path succeed
docker compose exec app sh -lc 'echo test > /tmp/test-file && cat /tmp/test-file'

# If using a dedicated data volume, verify that exact path remains writable
docker compose exec app sh -lc 'mkdir -p /app/data && echo test > /app/data/test-file && cat /app/data/test-file'
```