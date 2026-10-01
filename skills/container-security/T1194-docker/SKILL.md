---
name: no-ssh-in-containers-docker
description: Use when Dockerfiles, entrypoints, compose files, or docs install, expose, start, or recommend SSH access inside containers; remove container SSH and direct operators to host SSH plus nsenter.
---

# Do not run SSH within containers

## What This Skill Does
This skill removes SSH servers and SSH-based access patterns from Docker containers. It applies when a container image installs `openssh-server`, starts `sshd`, exposes port `22`, or documents SSH into the container as a supported workflow. The fix is to keep the container focused on the main application process, remove SSH startup and port exposure, and update operator guidance to SSH to the Docker host and use `nsenter` for container access when needed.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile or scripts install `openssh-server` or similar SSH server packages | Remove the SSH server install and related setup; keep only packages needed for the app |
| Entrypoint, CMD, supervisor config, or startup script starts `sshd` | Remove SSH process startup and make the main app process the only container process |
| Dockerfile, Compose, or runtime config exposes/maps port `22` | Remove `EXPOSE 22` and any `22:22` or equivalent port mappings |
| README, help text, or admin docs tell users to SSH into the container | Replace with guidance to SSH to the Docker host and use `nsenter` to enter the container |
| Container already runs only the application process and has no SSH service or SSH docs | No action needed |

## Boundaries

### Can Do
- Remove SSH server installation, configuration, and startup from Docker images and container scripts
- Remove container SSH port exposure and related configuration
- Update container access guidance to use host SSH plus `nsenter`

### Cannot Do
- Set up host-side SSH access, Docker host hardening, or operator account management
- Guarantee `nsenter` is available or permitted in the target environment
- Redesign workflows that depend on SSH for file transfer, orchestration, or debugging beyond replacing documented guidance

## Gotchas
- Removing `sshd` but keeping `EXPOSE 22`: this still advertises an SSH access path and should be removed
- Replacing `sshd` with process managers that still launch SSH indirectly: the container must start only the main app process
- Leaving docs or generated help text that says "SSH into the container": operators will keep using the insecure workflow even after code changes

## Quick Verification
```bash
# Find SSH server installs or startup
grep -RInE 'openssh-server|sshd|/usr/sbin/sshd|service ssh|systemctl start ssh' .

# Find SSH port exposure in Dockerfiles and Compose files
grep -RInE 'EXPOSE[[:space:]]+22|22:22|target:[[:space:]]*22|published:[[:space:]]*22' .

# Find docs or help text that instruct container SSH access
grep -RInE 'ssh into (the )?container|ssh root@|ssh .*container' .

# Review container startup commands
grep -RInE 'CMD|ENTRYPOINT|command:|entrypoint:' Dockerfile* docker-compose*.yml docker-compose*.yaml . 2>/dev/null
```