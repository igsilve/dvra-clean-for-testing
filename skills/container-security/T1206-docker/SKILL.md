---
name: docker-on-failure-restart-policy-5
description: Use when Docker Compose services must enforce the exact restart value on-failure:5 and reject missing or non-compliant restart settings.
---
# Set the 'on-failure' container restart policy to 5 (Docker)

## What This Skill Does
This skill fixes Docker Compose service configuration that omits `restart` or uses a non-compliant restart policy. It updates or validates Compose YAML so each intended service has the exact value `restart: on-failure:5`, while preserving other service settings and rejecting alternate modes, missing retry counts, malformed values, or retry limits other than `5`.

## Decision Table
| Situation | Action |
|-----------|--------|
| A Docker Compose service is missing the `restart` field | Add `restart: on-failure:5` for the intended service |
| A service uses `restart: always`, `unless-stopped`, `no`, or any value other than `on-failure:5` | Replace it with the exact value `on-failure:5` |
| A service uses `restart: on-failure` without a retry count, or `on-failure:N` where `N != 5` | Reject or rewrite it to `on-failure:5`, depending on whether the code validates or generates config |
| Code generates or rewrites Compose service definitions | Ensure it writes `restart: on-failure:5` exactly and preserves unrelated fields |
| The service already has `restart: on-failure:5` | No action needed |

## Boundaries

### Can Do
- Update Compose YAML service definitions to set `restart: on-failure:5`
- Add validation that requires the `restart` field and exact value `on-failure:5`
- Preserve other service keys while changing only the restart policy for intended services

### Cannot Do
- Decide which services are in scope if the application does not define that
- Guarantee runtime behavior outside the Compose configuration itself
- Fix Docker Swarm `deploy.restart_policy` settings, which are different from Compose `restart`

## Gotchas
- Using `on-failure` without `:5`: this is non-compliant because the retry limit is required
- Accepting `on-failure:3` or any count other than `5`: this still fails the requirement
- Editing `deploy.restart_policy` instead of service-level `restart`: this changes a different setting and may not fix the actual issue

## Quick Verification
```bash
# Show restart values in a compose file
grep -n "restart:" docker-compose.yaml

# Validate that only the exact required value is present for expected services
python - <<'PY'
import sys, yaml
data = yaml.safe_load(open("docker-compose.yaml"))
services = data.get("services", {})
bad = []
for name, svc in services.items():
    if svc.get("restart") != "on-failure:5":
        bad.append((name, svc.get("restart")))
if bad:
    print("Non-compliant services:", bad)
    sys.exit(1)
print("All services use restart: on-failure:5")
PY

# Negative check examples: should find non-compliant values if present
grep -nE 'restart:\s*("?always"?|"?unless-stopped"?|"?on-failure"?|"?on-failure:[^5]"?)' docker-compose.yaml || true
```