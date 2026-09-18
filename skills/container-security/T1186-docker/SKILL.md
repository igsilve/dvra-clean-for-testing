---
name: do-not-store-secrets-in-dockerfiles
description: Use when Dockerfiles or Docker build-generation code hardcode secrets in ARG, ENV, LABEL, RUN, or inline shell commands; removes embedded secrets, moves runtime secrets to container startup, and uses transient build secrets for required build-time access.
---

# Do not store secrets in Dockerfiles

## What This Skill Does
This skill removes hardcoded secrets from Dockerfiles and Docker build-generation code so credentials do not end up in image layers, metadata, build history, or generated build content. Apply it when secrets appear in `ARG`, `ENV`, `LABEL`, `RUN`, inline shell fragments, or generated Docker build commands. Fixes include rejecting embedded secret values, requiring application secrets at runtime with fail-closed behavior, and using Docker BuildKit secret mounts for build steps that truly need secret access.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile contains secret-like values in `ARG`, `ENV`, `LABEL`, `RUN`, or inline shell commands | Remove the secret from the Dockerfile and reject secret-bearing build content |
| Application or script generates Dockerfiles or `docker build` commands with secret values | Centralize validation and block writing or executing secret-bearing content |
| Container needs application secrets such as DB passwords or API keys | Load them at runtime from external input and fail closed if missing, empty, or placeholder |
| Build step needs a secret to fetch dependencies or access a private resource | Replace `ARG`/`ENV` usage with a BuildKit `RUN --mount=type=secret,...` pattern and avoid persisting the secret |
| Dockerfile already avoids embedded secrets and uses runtime/env or build secrets safely | No action needed |

## Boundaries

### Can Do
- Remove hardcoded secrets from Dockerfile instructions and generated build content
- Convert build-time secret handling from `ARG`/`ENV` to transient BuildKit secret mounts
- Enforce runtime secret loading that fails when required values are missing or empty

### Cannot Do
- Provision or manage the external secret source used at runtime
- Guarantee downstream application code will not log or persist secrets after startup
- Recover or rotate secrets that were already exposed in image history, registries, or prior builds

## Gotchas
- Leaving secrets in `ARG` because they are "build-only": `ARG` values can still leak through build history and generated build configuration
- Using runtime fallbacks like `DB_PASSWORD=${DB_PASSWORD:-devsecret}`: fallback secrets reintroduce hardcoded credentials and must be rejected
- Using BuildKit secrets but writing them to files or exported artifacts: this defeats the transient secret mechanism and can persist the secret in layers

## Quick Verification
```bash
# Find likely secret-bearing Dockerfile instructions
grep -RniE '^(ARG|ENV|LABEL|RUN).*?(secret|token|password|passwd|api[_-]?key|access[_-]?key)' .

# Build should not require hardcoded secrets in the Dockerfile
docker build -t test-image .

# Runtime should fail closed when required secret is missing or empty
docker run --rm test-image || true
docker run --rm -e DB_PASSWORD='' test-image || true

# Runtime should start only when the secret is provided externally
docker run --rm -e DB_PASSWORD='example-runtime-value' test-image

# If build-time secret is required, verify BuildKit secret usage
DOCKER_BUILDKIT=1 docker build --secret id=pip_token,src=./pip_token.txt -t test-image .

# Check image history for obvious secret leakage
docker history --no-trunc test-image
```