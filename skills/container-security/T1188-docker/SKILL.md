---
name: configure-linux-security-modules-docker
description: Configure AppArmor-aware Python/Flask containers so they detect unconfined Docker execution and keep filesystem access within a constrained data root; use when fixing misconfigured or disabled Linux Security Modules in Dockerized apps.
---

# Configure Linux Security Modules (Docker)

## What This Skill Does
This skill helps Dockerized Python/Flask services avoid running without expected Linux Security Module (LSM) confinement (AppArmor) and keeps their filesystem access predictable. It adds runtime checks that fail fast if AppArmor is disabled or the profile is unexpected, constrains file I/O to a single data root suitable for AppArmor profiles, and provides a protected diagnostic endpoint to inspect confinement safely.

## Decision Table
| Situation | Action |
|-----------|--------|
| Docker run/compose uses `--security-opt apparmor=unconfined` or no clear profile is required | Document required AppArmor profile and add startup check that rejects `unconfined` in production |
| App code reads/writes arbitrary paths (e.g., `/tmp`, `/etc`, user-supplied paths) | Introduce a single configurable `APP_DATA_ROOT` and enforce all file I/O to stay under that directory |
| App needs to know whether it is actually confined (for ops/debug) | Add a read-only diagnostic endpoint exposing AppArmor profile, env, and data root, protected by a secret header token |
| Environment differences (dev vs prod) make strict checks painful | Gate strict AppArmor enforcement on `APP_ENV=production` and allow relaxed behavior elsewhere via env vars |
| Code already validates AppArmor profile and constrains file I/O to a data root | No action needed; only consider adding a protected diagnostic endpoint if visibility is missing |

## Boundaries

### Can Do
- Add or modify Python/Flask startup code to:
  - Read `/proc/self/attr/current`
  - Fail fast in production when profile is `unconfined` or missing
  - Optionally enforce an expected profile prefix via env var
- Introduce filesystem helpers that:
  - Resolve a single `APP_DATA_ROOT`
  - Normalize and validate requested paths
  - Reject directory traversal or access outside the allowed subtree
- Implement a low-privilege, token-protected diagnostic endpoint that:
  - Reports current AppArmor profile, data root, and environment
  - Does not allow runtime configuration changes

### Cannot Do
- Configure AppArmor itself from inside the Dockerfile or app (profile loading and attachment must be done by the orchestrator/host)
- Guarantee that AppArmor is enabled on the host or that specific profiles exist (can only detect and react at runtime)
- Replace a full security review of Docker flags (e.g., `--privileged`, extra capabilities); this skill focuses on LSM/AppArmor awareness and filesystem patterns

## Gotchas
- Treating dev like prod: Enforcing strict AppArmor checks unconditionally can break local/dev environments that lack AppArmor; always gate strict behavior on `APP_ENV=production`.
- Assuming `/proc/self/attr/current` always exists: On some platforms or when AppArmor is unavailable, this file may be missing or unreadable; code must handle `None` and only fail hard in production.
- Incomplete path validation: Checking for `"../"` substrings or using string prefix checks alone is unsafe; always use `Path.resolve()` and compare against the resolved `APP_DATA_ROOT` and its parents.

## Quick Verification
```bash
# 1) Build the mitigated Flask image
docker build -t secure-app:latest .

# 2) Run with AppArmor disabled (should FAIL in production)
docker run --rm \
  -e APP_ENV=production \
  --security-opt apparmor=unconfined \
  secure-app:latest

# 3) Run with an AppArmor profile (example: docker-default) (should START)
docker run -d --rm \
  -p 8080:8080 \
  -e APP_ENV=production \
  --security-opt apparmor=docker-default \
  secure-app:latest

# 4) Test path confinement (attempt traversal should FAIL)
curl -i "http://localhost:8080/data?name=../../etc/passwd" -d 'test'

# 5) Call diagnostic endpoint with and without token
curl -i http://localhost:8080/internal/apparmor_status           # expect 403
curl -i -H "X-Internal-Token: dev-token-override-me" \
  http://localhost:8080/internal/apparmor_status                 # expect JSON with profile/env/root
```