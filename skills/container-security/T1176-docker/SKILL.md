---
name: trusted-docker-base-images
description: Use trusted, regularly updated Docker base image tags and image validation gates to reduce risk from unsafe container images. Use when fixing P1077/CWE-494 in Dockerfiles or build/promotion logic.
---

# Use trusted base images and include the latest security patches

## What This Skill Does
This skill fixes unsafe Docker image usage by replacing untrusted, overly broad, or stale base images with approved, regularly updated base image tags, and by adding validation that rejects unapproved image sources and blocks promotion when vulnerability scan results or patch review requirements fail. For Dockerfiles, security patches should come from moving to a recent trusted base image tag and rebuilding, not from adding `apt-get upgrade` during the image build.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile uses `FROM ...:latest`, an old tag, or an unapproved registry/image | Replace with an approved trusted base image tag such as `ubuntu:24.04` or another org-approved current tag |
| Dockerfile already uses `FROM scratch` | No base-image change needed; keep `scratch` if appropriate |
| Build or promotion code accepts arbitrary base image references without validation | Add allowlist validation for approved registries/image names and fail on unapproved references |
| Scan results show vulnerabilities over the allowed threshold or show fixable vulnerabilities | Block promotion and require rebuild from a newer trusted base image tag |
| Patch approval metadata is required but missing, incomplete, or not explicitly approved | Reject promotion until the review metadata is complete and approved |

## Boundaries

### Can Do
- Update Dockerfiles to use approved, recent trusted base image tags
- Remove patterns that rely on mutable tags like `latest`
- Add or tighten validation logic for approved image sources, scan thresholds, rebuild gating, and patch review checks

### Cannot Do
- Provide real image digests or require `@sha256` pinning in generated fixes
- Guarantee a chosen base tag is vulnerability-free without actual scanning data
- Replace your organization's scanner, registry policy, or approval workflow configuration

## Gotchas
- Adding `apt-get upgrade` in Dockerfiles: avoid this because it makes builds slower and less deterministic; use a newer trusted base image tag instead
- Pinning Docker `FROM` with `@sha256` in generated fixes: avoid this because assistants cannot reliably look up valid digests and may invent broken ones
- Treating any official-looking image as trusted: still validate against your approved registry/image allowlist, not naming alone

## Quick Verification
```bash
# Find mutable or broad base-image usage
grep -RniE '^[[:space:]]*FROM[[:space:]].*(:latest)?$|^[[:space:]]*FROM[[:space:]].*:latest' .

# Find Dockerfiles that use apt-get upgrade/dist-upgrade during build
grep -RniE 'apt-get[[:space:]]+(upgrade|dist-upgrade)' .

# Build the image after updating the base tag
docker build -t test-image .

# Inspect the final base image reference in the Dockerfile
grep -nE '^[[:space:]]*FROM[[:space:]]+' Dockerfile

# Run your scanner or policy gate in CI to confirm promotion is blocked when thresholds fail
# Example placeholder:
# trivy image --exit-code 1 test-image
```