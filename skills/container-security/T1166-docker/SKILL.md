---
name: encrypt-inter-node-container-traffic-docker
description: Encrypt data exchanged between containers on different nodes on a Docker overlay network; use when inter-container traffic may traverse untrusted networks or currently uses plaintext protocols.
---

# Encrypt data exchanged between containers on different nodes on the overlay network (Docker)

## What This Skill Does
This skill detects and fixes cases where containers on different nodes communicate over plaintext (e.g., HTTP or raw TCP) across a Docker overlay network. It guides agents to enforce TLS for all cross-node service endpoints, validate peer identity, and centralize secure connection creation so that no sensitive data (credentials, tokens, business data) traverses the overlay in cleartext.

## Decision Table
| Situation | Action |
|-----------|--------|
| Dockerfile exposes a service on a plaintext port (e.g., 80/8080) intended for use by other containers across nodes | Replace the service configuration to listen only on a TLS-enabled port (e.g., 443/8443) and remove/stop exposing plaintext ports |
| Application code (HTTP, gRPC, custom TCP) is called by other services across nodes using non-TLS URLs or raw sockets | Wrap all such connections in TLS (HTTPS/grpcs/TLS sockets) and update clients to use the encrypted endpoints |
| TLS is enabled but client configuration skips certificate validation (e.g., `verify=False`, `insecureSkipVerify`, custom SSL contexts without CA) | Enforce certificate validation using a trusted CA or pinned certificates; remove insecure flags and weak contexts |
| Multiple services create raw sockets directly for inter-container communication | Introduce centralized secure connection helpers (e.g., `create_client_ssl_context`, `tls_client_connect`) and refactor callers to use them instead of raw sockets |
| Service already uses TLS with proper certificate validation for all cross-node traffic and no plaintext ports are exposed | No action needed |

## Boundaries

### Can Do
- Identify Dockerfiles and app code that expose or consume plaintext services intended for cross-node container communication.
- Add or configure TLS (e.g., HTTPS for Flask, TLS-wrapped sockets using Python’s `ssl` and `socket`) and adjust exposed ports/health checks accordingly.
- Introduce reusable connection-builder utilities so that all inter-container clients use encryption and certificate validation consistently.

### Cannot Do
- Provision or manage real certificate authorities, production-ready PKI, or secret distribution systems (e.g., Vault, cert-manager); assumes certs/keys will be mounted or generated securely by ops.
- Guarantee compliance with specific regulatory frameworks (e.g., PCI, HIPAA) beyond providing encrypted transport and sane defaults.
- Detect at runtime whether traffic stays on a single node vs. crosses nodes; it treats any inter-container service endpoint as potentially cross-node and secures it accordingly.

## Gotchas
- Generating long-lived self-signed certs inside the image: This is only acceptable for local/demo scenarios. In production, certificates and keys should be mounted at runtime or managed externally; otherwise, you bake secrets and rigid trust anchors into the image.
- Leaving the old plaintext port exposed “for backwards compatibility”: This undermines the fix because clients can keep using cleartext. Once TLS is added and tested, remove or block the plaintext endpoint (and update all clients).
- Enabling TLS but disabling verification (e.g., `curl --insecure` in client code, `verify=False` in HTTP libraries): This is not secure against active attacks. Use a CA bundle or pinned certs and ensure hostname/peer identity is validated; `--insecure` should be limited to local container health checks when no proper CA is available.

## Quick Verification
```bash
# 1. Build the secure image
docker build -t overlay-tls-service .

# 2. Run two containers on an overlay network (example using a simple Swarm or compose setup)
# Create overlay network (Swarm example)
docker network create --driver overlay --attachable overlay-net

# Deploy the service on one node
docker run -d --name overlay-service --network overlay-net -p 8443:8443 overlay-tls-service

# 3. Attempt plaintext HTTP (should fail or not be available)
curl -v http://localhost:8080/secret-data || echo "Plaintext endpoint not available (expected)"

# 4. Call the encrypted endpoint (should succeed)
curl -v --insecure https://localhost:8443/health

# 5. Capture traffic and confirm it is encrypted (payload not readable)
# In another terminal, capture on the Docker bridge / host interface
sudo tcpdump -i any port 8443 -A

# Send a request with sensitive data
curl -v --insecure https://localhost:8443/secret-data \
  -H "Content-Type: application/json" \
  -d '{"password": "SuperSecret123"}'

# Inspect tcpdump output to ensure no readable JSON/password appears in the capture
```