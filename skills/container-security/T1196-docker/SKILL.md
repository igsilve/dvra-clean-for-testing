---
name: open-only-needed-ports-on-the-containers-docker
description: "Reduce Docker container exposure by keeping only approved ports in EXPOSE and runtime mappings. Use when containers declare or publish ports the application does not need."
---
# Open only needed ports on the containers (Docker)

## What This Skill Does
This skill reduces container attack surface by removing unnecessary port declarations and published mappings from Dockerfiles and generated container configuration. Use it when a container exposes admin, debug, metrics, legacy, or inherited ports that the application does not actually listen on. The fix is to maintain a single approved list of listening ports, make `EXPOSE` and runtime port mappings match that list exactly, and reject unknown ports, including protocol-qualified values such as `80/tcp` or `5353/udp`.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile contains `EXPOSE` entries not used by the application | Remove unneeded ports and keep only the approved ports |
| Container config or templates generate published port mappings dynamically | Validate generated mappings against the approved port list and reject unknown ports |
| `EXPOSE` values include protocol suffixes like `/tcp` or `/udp` | Parse and validate port plus protocol consistently against the approved list |
| Dockerfile inherits stale ports from examples, templates, or older versions | Replace inherited declarations with the current approved ports only |
| Dockerfile and runtime mappings already match the approved listening ports | No action needed |

## Boundaries

### Can Do
- Remove unnecessary `EXPOSE` entries from Dockerfiles
- Align Dockerfile port declarations with an approved application port list
- Add validation so generated runtime mappings include only approved ports

### Cannot Do
- Determine the correct application ports without code, config, or team-defined requirements
- Prevent operators from manually publishing extra ports outside the repository
- Guarantee a service is unreachable if another proxy, sidecar, or host rule exposes it elsewhere

## Gotchas
- Treating `EXPOSE` as harmless metadata only: it still signals intended reachability and often gets copied into runtime configuration or review assumptions
- Validating only bare numbers like `80`: this misses protocol-qualified entries such as `80/tcp` or `5353/udp`
- Removing `EXPOSE` but leaving `ports:` or `-p` mappings in Compose or run scripts: the container can still be published at runtime

## Quick Verification
```bash
# Find Dockerfiles and EXPOSE declarations
find . -iname 'Dockerfile*' -o -name '*.dockerfile' | xargs grep -nE '^\s*EXPOSE\s+'

# Find common runtime port mappings in Compose files
find . \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) \
  | xargs grep -nE '^\s*ports:|-\s*"[0-9]+:[0-9]+'

# Build and inspect exposed ports declared in the image
docker build -t port-check .
docker image inspect port-check --format '{{json .Config.ExposedPorts}}'

# Negative test: add an unapproved port such as 9000 and confirm validation or review rejects it
grep -R -nE '9000(/tcp|/udp)?|9000:9000' .
```