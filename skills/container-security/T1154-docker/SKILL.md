---
name: secure-docker-registries
description: Secure Docker registries (Docker) by enforcing TLS, trusted CAs, and no insecure registries; Use when code or Dockerfiles interact with container registries
---

# Secure Docker registries (Docker)

## What This Skill Does
Enforces that Docker images are only pulled from or pushed to TLS-protected registries with proper certificate verification and trusted CAs. It removes insecure (`http://`) registry usage, prevents “insecure registry” flags or fallbacks in production, and documents/validates the expected CA location on Docker hosts so that registry communication cannot be intercepted or tampered with.

## Decision Table
| Situation | Action |
|-----------|--------|
| `FROM http://...` or any registry URL using `http` (plaintext) is found | Replace with an `https`-based registry or an approved TLS-protected image (e.g., `FROM alpine:3.20` from Docker Hub) and remove any plaintext registry usage |
| Code, scripts, or config use `--insecure-registry`, `insecure-registries`, or flags that disable TLS/cert verification in production | Remove those flags/options for production paths; make production fail fast when such settings are present |
| Code constructs registry URLs dynamically (e.g., `REGISTRY_URL`, `REGISTRY_HOST`) | Force `https://` scheme in those URLs, and ensure no downgrade to `http` is possible in production |
| Images are expected to use a private registry with a custom CA | Document and enforce `/etc/docker/certs.d/<registry-name>/ca.crt` as the CA path via env vars/labels; rely on Docker host to provide the CA and treat missing CA as configuration error |
| Registry access is already using `https` with no insecure flags and no plaintext endpoints | No action needed; optionally add labels/metadata documenting TLS and CA requirements for policy tools |

## Boundaries

### Can Do
- Detect and remove obvious insecure registry usage in Dockerfiles (e.g., `FROM http://insecure-registry...`).
- Guide replacement with secure, TLS-enabled registries and official base images (e.g., `FROM alpine:3.20`).
- Add metadata (labels, env vars, args) that encode “HTTPS-only”, “TLS-verify required”, and CA path expectations for registries.

### Cannot Do
- Cannot verify that a given registry actually has TLS correctly configured or that its CA is properly installed on the host (this requires runtime/ops checks).
- Cannot generate or manage real TLS certificates or CA files; only document and reference their expected locations.
- Cannot update Docker daemon or orchestration platform settings directly (e.g., removing `--insecure-registry` from dockerd flags); can only suggest configuration changes.

## Gotchas
- Allowing `http://` in non-production code “for convenience”: this often bleeds into production via shared Dockerfiles or CI pipelines; keep Dockerfiles and shared scripts HTTPS-only and enforce environment-based checks in higher-level code instead.
- Disabling certificate or hostname verification “temporarily” (e.g., `tls-verify=false`, custom HTTP client flags): this silently breaks the trust model even though `https` is used; always treat disabled verification as insecure in production.
- Assuming CA files inside the image control Docker’s pull behavior: Docker uses CA certificates on the *host* under `/etc/docker/certs.d/<registry-name>/`; placing CAs only inside the container does not secure `docker pull` operations.

## Quick Verification
```bash
# 1. Static check: search for insecure registry usage in Dockerfiles and configs
grep -R --line-number --color=always -E 'FROM http://|--insecure-registry|insecure-registr' .

# 2. Ensure base images use HTTPS/TLS-protected registries (no http:// in image references)
grep -R --line-number --color=always 'http://' Dockerfile docker-compose*.yml || echo "No plaintext registries found"

# 3. Verify Docker host CA layout for a private registry (replace with your registry name)
REGISTRY_NAME="registry.example.com"
ls -l "/etc/docker/certs.d/${REGISTRY_NAME}/" || echo "Missing Docker registry CA directory"
test -s "/etc/docker/certs.d/${REGISTRY_NAME}/ca.crt" && echo "CA file present and non-empty" || echo "CA file missing or empty"

# 4. Attack test: try to build from a plaintext registry (should fail by policy/CI)
docker build -f vulnerable.dockerfile . || echo "Build blocked as expected for insecure registry"
```