---
name: do-not-expose-unnecessary-host-resources-docker
description: "Prevents Docker and Compose configs from exposing host filesystems, namespaces, devices, or the Docker socket. Use when code generates, accepts, merges, or validates container runtime settings."
---

# Do not expose unnecessary host resources (Docker)

## What This Skill Does
This skill fixes unsafe Docker and Docker Compose configuration that breaks container isolation by exposing host filesystems, namespaces, devices, or the Docker daemon socket. Apply it where container configuration is created, transformed, merged, or validated so unsafe inputs are rejected before deployment. The fix is to validate effective service configuration, normalize mount source paths, block sensitive host bind mounts and Docker socket mounts, reject host namespace sharing (`pid`, `ipc`, `uts`, `userns_mode` set to `host`), and reject device passthrough fields.

## Decision Table
| Situation | Action |
|-----------|--------|
| A service defines `volumes`, `mounts`, or bind mounts from host paths | Parse short and long syntax, normalize source paths, and reject sensitive sources such as `/`, `/boot`, `/dev`, `/etc`, `/lib`, `/proc`, `/sys`, `/usr`, and `/var/run/docker.sock` |
| A service uses `pid`, `ipc`, `uts`, or `userns_mode` | Reject the configuration if any of these fields is set to `host`; otherwise allow omitted or non-host values |
| A service defines `devices` or `device_cgroup_rules` | Reject the configuration when these fields exist and are non-empty |
| Configuration is assembled from templates, defaults, or overrides | Validate the final merged service definition, not just the original input fragments |
| The service already uses named volumes or approved non-sensitive paths and does not share host namespaces or devices | No action needed |

## Boundaries

### Can Do
- Add validation that rejects sensitive host bind mounts and Docker socket exposure
- Enforce rejection of `pid: host`, `ipc: host`, `uts: host`, and `userns_mode: host`
- Block direct device mappings and `device_cgroup_rules` in Docker or Compose service definitions

### Cannot Do
- Decide which non-sensitive host paths are safe for a specific business need without a project-defined allowlist
- Remove all Docker risk by itself; other dangerous settings such as `privileged: true` may need separate controls
- Guarantee runtime safety if containers are launched outside the validated code path

## Gotchas
- Only checking string prefixes on mount paths: equivalent paths like `/etc/../etc` or repeated slashes can bypass naive checks unless paths are normalized first
- Validating only one mount format: Compose supports short and long syntax, so checking only `source:` or only `host:container` strings misses cases
- Validating before merges only: defaults or overrides can reintroduce `pid: host` or a sensitive mount after the first validation pass

## Quick Verification
```bash
# Reject Docker socket and sensitive host mounts
cat > compose.bad-mounts.yml <<'YAML'
services:
  app:
    image: alpine:3.19
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /etc:/host-etc:ro
YAML

# Reject host namespace sharing
cat > compose.bad-namespaces.yml <<'YAML'
services:
  app:
    image: alpine:3.19
    pid: host
    ipc: host
    uts: host
    userns_mode: host
YAML

# Reject device passthrough
cat > compose.bad-devices.yml <<'YAML'
services:
  app:
    image: alpine:3.19
    devices:
      - /dev/null:/dev/null
    device_cgroup_rules:
      - 'c 1:3 rwm'
YAML

# Replace with your app's validation command or test suite
./your-validator compose.bad-mounts.yml
./your-validator compose.bad-namespaces.yml
./your-validator compose.bad-devices.yml
```