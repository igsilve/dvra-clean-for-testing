---
name: confirm-cgroup-usage-docker
description: Use when Docker or Compose configuration must verify each container runs under an exact expected cgroup and fail closed on missing or unverifiable runtime metadata.
---

# Confirm cgroup usage (Docker)

## What This Skill Does
This skill fixes cases where Docker containers are allowed to run without confirming they are assigned to the required cgroup. It adds explicit cgroup configuration, stores expected cgroup identities in configuration, and verifies runtime metadata against exact expected values or an allowed set. The check must fail closed if inspection fails, returns malformed data, or does not provide a cgroup value.

## Decision Table
| Situation | Action |
|-----------|--------|
| Docker Compose services have no explicit `cgroup_parent` | Add an exact `cgroup_parent` value per service and store the expected value in configuration |
| Code or scripts only check that a container is running, not which cgroup it uses | Add a runtime inspection step that compares the actual cgroup to an exact expected value or allowed set |
| Runtime inspection uses loose string matching such as "contains" or non-empty checks | Replace with exact equality or membership checks against configured values |
| Runtime metadata is missing, malformed, or inspection fails | Return fail for that container and stop treating it as compliant |
| Containers already define exact cgroup values and verification is deterministic | No action needed |

## Boundaries

### Can Do
- Add explicit `cgroup_parent` settings to Docker Compose services
- Introduce exact expected cgroup values through configuration
- Add or update verification logic to fail closed on missing or invalid cgroup data

### Cannot Do
- Guarantee the host runtime, orchestrator, or kernel will honor unsupported cgroup settings
- Infer the correct expected cgroup value without project-specific requirements
- Replace broader container isolation controls beyond confirming cgroup assignment

## Gotchas
- Using loose checks like "value exists" or substring matching: this can pass the wrong cgroup and makes verification non-deterministic
- Treating inspection errors as warnings: this is wrong because the countermeasure requires fail-closed behavior
- Setting `cgroup_parent` but never verifying it at runtime: configuration alone does not confirm the container actually runs under that cgroup

## Quick Verification
```bash
# Start the Compose stack
docker compose up -d

# Inspect cgroup parent values for containers in the project
docker ps --format '{{.Names}}' | while read c; do
  echo "== $c =="
  docker inspect --format '{{.Name}} {{.HostConfig.CgroupParent}}' "$c"
done

# Verify one expected match directly
docker inspect --format '{{.HostConfig.CgroupParent}}' <container-name>

# Negative test: a missing, empty, or unexpected value must be treated as fail
docker inspect --format '{{.HostConfig.CgroupParent}}' <container-name> | grep -Fx 'app.slice'
```