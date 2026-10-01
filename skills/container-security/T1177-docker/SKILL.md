---
name: verify-secure-updated-docker-images
description: Ensure Dockerfiles and container-using code rely only on trusted, pinned, and security-validated images; use when code builds, pulls, or runs Docker images that may be unsafe or outdated
---

# Verify that secure and updated images are used (Docker)

## What This Skill Does
Helps detect and fix use of unsafe Docker images by enforcing trusted registries/namespaces, explicit non-`latest` tags, and integration with image scanning and package metadata checks. It guides changes in Dockerfiles and surrounding application/orchestration code so containers run from verifiable, up-to-date, and approved images instead of arbitrary or unpinned ones.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile uses `FROM some-image:latest` or an unpinned tag (no clear version) | Replace with a trusted registry/namespace and a pinned, approved tag (e.g., `FROM registry.example.com/trusted/alpine:3.20`) and document/label image approval policy |
| Image is pulled from a public or user-controlled registry without validation | Add identifier allow-listing (registry, namespace, repository) in app/orchestrator code; reject any image not on the allow-list before pulling or running |
| Application accepts image names/tags from config, env vars, or API requests | Treat all image references as untrusted input; add strict pattern validation and map logical image names to a small, hard-coded set of approved images |
| CI/CD builds or runs images without vulnerability gating | Integrate image scanner results (e.g., via build args like `VULN_SCAN_STATUS=clean`); fail the build or deployment when severity thresholds or CVE policies are violated |
| Application manages containers for sensitive workloads but never inspects packages inside them | Add package inventory generation (e.g., `apk info -v > /opt/package-inventory.txt`) or use OS-specific metadata APIs; enforce minimum versions / “no critical CVEs” before use |
| Code already uses a trusted, pinned image from an internal registry and is gated by scanning and policy checks | No action needed beyond keeping tags current and policies in sync with security requirements |

## Boundaries

### Can Do
- Identify and replace insecure base images in Dockerfiles (e.g., `ubuntu:latest`) with trusted, pinned tags from approved registries.
- Suggest patterns for allow-listing registries/namespaces/repositories and validating image references in app or orchestrator code.
- Add simple build-time gates (via `ARG` and labels) that tie images to scanner results, digests, or inventory artifacts for external policy enforcement.

### Cannot Do
- Cannot run actual vulnerability scanners or confirm that a specific real-world image is free of CVEs.
- Cannot determine your organization’s true list of trusted registries or required version ranges; can only propose placeholders and patterns.
- Cannot modify external infrastructure (Kubernetes, CI systems, registries); recommendations must be implemented by developers or ops engineers.

## Gotchas
- Assuming `ubuntu:latest` or other `:latest` tags are “up to date and secure”: tags change over time and may introduce new vulnerabilities; always pin to a specific, supported version tag.
- Relying only on comments to enforce scanning or policy: documentation without code-level gates (build args, labels, policy checks) won’t stop unsafe images from being used.
- Validating only part of the image reference (e.g., just the repository name) and ignoring registry/namespace and tag: attackers can abuse lookalike registries or tags; always validate the full structured reference (registry, namespace, name, tag/digest).

## Quick Verification
```bash
# 1. Check for unpinned or latest tags in Dockerfiles
grep -R --line-number -E 'FROM .*:latest|FROM [^@: ]+$' .

# 2. Confirm trusted, pinned base images are used
grep -R --line-number -E 'FROM ' Dockerfile* | sed 's/^/DOCKERFILE FROM: /'

# 3. Build with security gates to ensure they work
docker build \
  --build-arg IMAGE_SECURITY_STATUS=approved \
  --build-arg VULN_SCAN_STATUS=clean \
  -t secure-image:test .

# Expect failure if args are not set or not "approved"/"clean"
docker build -t secure-image:should-fail . || echo "Build correctly failed due to security gate"

# 4. Inspect labels and package inventory in the built image (if configured)
docker inspect secure-image:test | jq '.[0].Config.Labels'
docker run --rm secure-image:test cat /opt/package-inventory.txt 2>/dev/null || echo "No inventory file present"
```