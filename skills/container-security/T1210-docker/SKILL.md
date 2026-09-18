---
name: configure-seccomp-profile-docker
description: Use when Docker or Compose config disables seccomp or accepts unsafe seccomp settings; keeps Docker default seccomp enabled or restricts custom profiles.
---

# Configure seccomp profile (Docker)

## What This Skill Does
This skill fixes Docker container configurations that expose too many kernel syscalls by disabling seccomp filtering or by allowing unsafe seccomp values. It keeps Docker’s default seccomp profile enabled for normal containers, rejects `seccomp=unconfined`, and supports custom seccomp profiles only when they are explicitly approved and remain restrictive by default.

## Decision Table
| Situation | Action |
|-----------|--------|
| Docker or Compose config uses `seccomp=unconfined` or `seccomp:unconfined` | Replace it with `seccomp=default`, or switch to an approved custom seccomp profile if the app truly needs extra syscalls |
| Code generates container args or `security_opt` values from user input | Add allowed-value validation so seccomp mode can only be `default` or an approved custom profile reference |
| A container needs syscalls blocked by Docker’s default seccomp profile | Use a vetted custom seccomp profile derived from the default profile; keep a restrictive default action |
| Custom seccomp profile path or identifier is not on the approved list | Reject the configuration instead of passing it through |
| Container config already uses Docker default seccomp or an approved restrictive custom profile | No action needed |

## Boundaries

### Can Do
- Replace insecure seccomp settings in Docker Compose or generated container options
- Enforce `default` or approved custom seccomp values in application configuration code
- Point containers to approved custom seccomp profile files when justified

### Cannot Do
- Determine which extra syscalls an application truly needs without app-specific evidence
- Audit a custom seccomp JSON profile for correctness beyond basic restrictive-policy checks
- Guarantee runtime enforcement if deployment tooling ignores or overrides the configured seccomp settings

## Gotchas
- Using `seccomp=unconfined` as a quick compatibility fix: this removes syscall filtering entirely and reopens unnecessary kernel attack surface
- Accepting arbitrary profile paths from config or user input: this lets callers bypass the approved seccomp policy
- Creating a custom profile with an allow-all default action: this defeats the purpose of seccomp even if a profile file is present

## Quick Verification
```bash
# Find insecure seccomp settings in Compose or config files
grep -RInE 'seccomp[=:]unconfined' .

# Find explicit seccomp settings to review
grep -RInE 'security_opt|seccomp[=:](default|[^[:space:]]+)' .

# Render Compose config and inspect the final security options
docker compose config

# Optional: reject unexpected custom profile references in app config
grep -RInE 'seccomp' .
```