---
name: configure-tls-auth-for-docker-daemon
description: Securely configure Docker daemon and Swarm endpoints with TLS authentication; use when Docker is exposed over TCP or additional sockets and must be locked down
---

# Configure TLS authentication for the Docker daemon (Docker)

## What This Skill Does
Locks down Docker Engine (and optional Swarm) access by enforcing TLS (preferably mutual TLS) on any network-exposed daemon endpoint and by avoiding unnecessary IP/port bindings. It guides agents to remove insecure `dockerd` TCP listeners (like `0.0.0.0:2375` without TLS), enforce certificate verification and client auth when TCP is required, and ensure TLS keys/certs are handled as secrets instead of being baked into images or exposed via logs.

## Decision Table
| Situation | Action |
|-----------|--------|
| Docker daemon is started with `--host=tcp://0.0.0.0:2375` or any TCP host and no `--tls*` flags | Replace with a TLS-only configuration on port 2376 (or policy-approved port) using `--tlsverify`, `--tlscacert`, `--tlscert`, and `--tlskey`, or revert to Unix socket only |
| Dockerfile or service config binds additional `--host=tcp://...` or extra Unix sockets beyond the default | Remove extra bindings; default to the standard Unix socket only unless a TLS-protected TCP endpoint is explicitly required |
| App/client code connects to Docker using `tcp://host:2375` or `http://` without certificate validation | Update to `https://` / `tcp+tls` endpoint on 2376 (or policy port), require CA validation, and configure client certificate authentication if the daemon uses mTLS |
| Environment requires remote daemon or Swarm access over the network | Configure `dockerd` (and Swarm settings) with TLS + client auth for all network endpoints, ensuring a consistent TLS configuration and no HTTP/plaintext fallbacks |
| TLS certificates/keys are copied into the image or stored in source control | Refactor to load TLS materials from runtime-mounted secrets/volumes, restrict file permissions at startup, and exclude keys from logs and image layers |
| Daemon is already only on default Unix socket and no code adds TCP access | No action needed; keep daemon local and rely on socket permissions |

## Boundaries

### Can Do
- Detect and remove insecure `dockerd` TCP bindings (e.g., `0.0.0.0:2375` without TLS) in Dockerfiles and service config snippets.
- Add secure TLS/mTLS `dockerd` flags for network-exposed daemons and Swarm endpoints, using secret-mounted certificate paths.
- Adjust example client connection strings and code snippets to require TLS, certificate validation, and (when appropriate) client certificates.
- Enforce use of default Unix socket only when remote access is not required, by dropping extra `--host` bindings and `EXPOSE` directives.

### Cannot Do
- Generate real, valid certificates or decide exact PKI/CA hierarchy and rotation policy; expects those to be provided by operators or external tooling.
- Reconfigure host-level Docker installations outside the visible code/config snippets (e.g., systemd units, `/etc/docker/daemon.json` not shown to the agent).
- Guarantee compatibility with every orchestration or CI platform’s Docker-in-Docker pattern; final integration and operational rollout remain human decisions.
- Inspect live network state or actively probe running hosts/containers; relies only on the provided files and configuration.

## Gotchas
- Assuming `--tlsverify` alone is enough: missing or misconfigured `--tlscacert`, `--tlscert`, or `--tlskey` can still leave the daemon inaccessible or missecured; always specify the full TLS set and ensure paths point to mounted secrets, not image-baked keys.
- Keeping both insecure and secure ports: adding a TLS listener on 2376 but leaving `--host=tcp://0.0.0.0:2375` (or similar) in place leaves a backdoor; remove all plaintext listeners when enabling TLS.
- Exposing Docker daemon when not needed: adding TCP exposure “for convenience” in development images or CI jobs often becomes permanent; prefer the default Unix socket and only add a TLS-protected TCP endpoint when a real remote requirement exists.

## Quick Verification
```bash
# 1) Confirm dockerd is NOT listening on insecure TCP ports (e.g., 2375)
ss -lntp | grep dockerd || netstat -lntp | grep dockerd || true

# 2) If TCP is required, confirm only TLS port (e.g., 2376) is open
ss -lntp | grep ':2376' || netstat -lntp | grep ':2376' || true

# 3) Test that unauthenticated TCP access fails
DOCKER_HOST=tcp://localhost:2376 \
  docker --tlsverify --tlscacert=bad-ca.pem version || echo "Unauthenticated/invalid cert access correctly denied"

# 4) Test that properly authenticated TLS access succeeds (paths adjusted to real secrets)
DOCKER_HOST=tcp://localhost:2376 \
  docker --tlsverify \
    --tlscacert=/run/secrets/ca.pem \
    --tlscert=/run/secrets/client-cert.pem \
    --tlskey=/run/secrets/client-key.pem \
    version
```