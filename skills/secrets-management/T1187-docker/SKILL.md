---
name: test-if-secrets-are-stored-in-dockerfiles-docker
description: Detects hard-coded secrets in Dockerfiles and Docker image history; Use when checking container build artifacts for embedded credentials or tokens
---

# Test if secrets are stored in Dockerfiles (Docker)

## What This Skill Does
This skill helps detect secrets that are accidentally stored in Dockerfiles or baked into Docker image layers. It focuses on pattern-based scanning of Dockerfile instructions and Docker image history (`CreatedBy` commands) to flag potential credentials, API keys, tokens, and passwords so builds or CI pipelines can fail before shipping images with embedded secrets.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfiles exist in the repository and are part of build/CI | Add a secret scanner step that parses all Dockerfiles and fails on any potential secret match |
| Docker images are built or pulled in CI/locally and may contain secrets in history | Inspect `docker history --no-trunc` for each relevant image and scan `CreatedBy` fields for secret patterns |
| Dockerfile contains `ENV`, `ARG`, or `RUN` with inline credentials or long random-looking strings | Treat as “potential secrets detected”; fail the build and require removal/relocation of secrets |
| Dockerfiles only reference secrets via build-time/ runtime mechanisms (e.g., build args from CI secrets, env vars injected at run, external secret managers) and no patterns trigger | Classify as “no secrets detected”; no blocking action needed |
| Docker images cannot be listed or history cannot be retrieved (permission/daemon errors) | Do not silently pass; surface an explicit error state and treat scan as failed/incomplete |

## Boundaries

### Can Do
- Scan Dockerfiles for obvious secret indicators (e.g., `ENV PASSWORD=...`, `ARG API_KEY=...`, long high-entropy literals in `RUN` commands).
- Normalize multi-line Docker instructions and comments to make scanning more reliable.
- Inspect Docker image history (`docker history --no-trunc`) and flag layers whose build commands likely embed secrets.
- Produce deterministic, machine-readable pass/fail results with file paths, line numbers, and pattern types.

### Cannot Do
- Prove with certainty that a suspicious value is or is not a real secret; it only flags likely patterns.
- Recover or scrub secrets already published in image registries or commit history; it only detects, it does not rotate or revoke.
- Detect secrets that are only injected at runtime (e.g., via `docker run -e` or orchestrator secret stores) since they never appear in Dockerfiles or image history.
- Guarantee full coverage when access to Docker artifacts is limited (e.g., no access to Docker daemon, remote registry, or some Dockerfiles are excluded from scanning).

## Gotchas
- Assuming comments are always safe: secrets are sometimes pasted into comments; scanners should optionally include comments instead of stripping them unconditionally.
- Ignoring multi-line Docker instructions (`ENV`/`RUN`/`LABEL` split with `\`): scanning per-line without reconstructing the full instruction can miss secrets or report confusing line locations.
- Treating scanner errors as “no secrets found”: failing to list images or retrieve history must be reported as an error, not success, or you risk silently skipping vulnerable images.

## Quick Verification
```bash
# 1) Create a vulnerable Dockerfile
cat > Dockerfile.vuln << 'EOF'
FROM python:3.12-slim
ENV DB_PASSWORD=SuperSecretP@ssw0rd
ARG GIT_TOKEN=ghp_exampleSuperSensitiveToken
RUN export API_KEY=sk_test_1234567890abcdef
EOF

# 2) Run a secret scanner against the vulnerable Dockerfile
detect-secrets scan Dockerfile.vuln

# 3) Build an image with an inline secret in a RUN/ENV/ARG layer
docker build -f Dockerfile.vuln -t secret-test-image .

# 4) Inspect image history and scan the CreatedBy commands
docker history --no-trunc secret-test-image | sed '1d' > history.txt
detect-secrets scan history.txt

# 5) Create a clean Dockerfile and confirm it passes
cat > Dockerfile.clean << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY app.py /app/app.py
CMD ["python", "app.py"]
EOF

detect-secrets scan Dockerfile.clean
```