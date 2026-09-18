---
name: do-not-use-aufs-storage-driver-docker
description: Enforce a no-aufs policy in Dockerized applications by detecting the aufs storage driver at runtime and failing fast; use when code may run on unknown Docker hosts or storage drivers.
---

# Do not use the aufs storage driver (Docker)

## What This Skill Does
This skill helps you detect when an application is running on Docker with the `aufs` storage driver and enforce a strict “no aufs” policy. It guides you to add lightweight, dependency-free runtime checks (entrypoint guards, startup checks, health endpoints, and CLI-style checks) that abort startup or report failure when `aufs` is detected, while keeping behavior safe and predictable when mount information is missing or unreadable.

## Decision Table
| Situation | Action |
|-----------|--------|
| Application may run in Docker on unknown hosts/storage drivers | Add a startup guard that inspects `/proc/self/mountinfo` and exits non-zero if `aufs` is detected before the app binds to any port. |
| There is a central entrypoint or application factory | Wrap the app with a small shell (or language-native) entrypoint that runs the `aufs` check first and fails fast with a clear message if `aufs` is detected. |
| Operators or orchestration need to confirm storage driver via HTTP | Expose a read-only health/diagnostics endpoint or mode (e.g., `/healthz` or `healthz` subcommand) that returns `aufs_detected` boolean and appropriate HTTP/exit status. |
| CI/CD, hooks, or external tools must enforce storage policy | Provide a pure function or CLI subcommand (e.g., `check-storage`) that runs the same `aufs` detection logic and exits 0 (no `aufs`) or 1 (aufs detected/error). |
| Code already detects unsafe storage drivers and fails on `aufs` | Do not add duplicate guards; verify coverage and clarity of error messages, then leave implementation as-is. |

## Boundaries

### Can Do
- Add or modify entrypoint/startup scripts to check `/proc/self/mountinfo` for `aufs` and abort startup when detected.
- Introduce a small, dependency-free utility or function that encapsulates the detection logic and is reusable from multiple call sites (startup, health checks, automation).
- Add read-only health/diagnostic endpoints or command modes that expose an `aufs`-status flag and suitable status code for monitoring and CI.

### Cannot Do
- Change the Docker daemon or host-level storage driver configuration (e.g., switch the host from `aufs` to `overlay2`); this must be done by operators.
- Reliably detect all container runtimes or custom storage stacks that do not expose usable mount information; in these cases the app can only infer based on available data.
- Guarantee that `grep`/mount parsing works on every non-Linux or heavily restricted environment where `/proc` is missing, virtualized, or locked down.

## Gotchas
- Treating unreadable `/proc/self/mountinfo` as “no aufs”: This is unsafe because the app would continue in an unknown state; instead, treat missing or unreadable metadata as a policy violation and fail closed when enforcing security rules.
- Burying the check in a rarely used code path: If the `aufs` guard is only called from one startup flow, alternative entrypoints or scripts can bypass it; always place enforcement in the single, central startup/entrypoint path.
- Returning detailed system information from health checks: Overly verbose diagnostics (full mount output, environment variables, etc.) can leak sensitive data; expose only a minimal `aufs` status flag and generic operator guidance.

## Quick Verification
```bash
# 1) Build an image with an entrypoint guard (example Dockerfile adjusted for your app)
docker build -t no-aufs-guard .

# 2) Run the image normally on a non-aufs host; it should start successfully
docker run --rm no-aufs-guard

# 3) Simulate/validate aufs detection logic locally (without real aufs) by faking mountinfo:
#    Create a test mountinfo file containing "aufs" and point the checker at it if supported,
#    OR run the guard script directly with a temporary file.
docker run --rm -v "$PWD/test-mountinfo:/tmp/mountinfo" no-aufs-guard sh -c '
  sed "s@/proc/self/mountinfo@/tmp/mountinfo@" /docker-entrypoint.sh > /tmp/test-entrypoint.sh &&
  sh /tmp/test-entrypoint.sh || echo "Guard correctly failed on simulated aufs"
'

# 4) For health/CLI modes, confirm exit codes:
docker run --rm no-aufs-guard check-storage || echo "CI would fail here on aufs"
```