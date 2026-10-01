---
name: t374-offload-http-request-handling-to-dedicated-modules
description: Move HTTP request handling concerns such as TLS termination, compression, header normalization and static delivery onto a dedicated front-end module.
---

### Task T374: Offload HTTP request handling to dedicated modules (DOCUMENTATION ONLY)

**Category:** INFRA
**SD Elements:** [T374](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T374/)
**Priority:** 7

**Guidance:** Dedicated, hardened modules should handle the protocol-level work rather than the application process: a reverse proxy terminating TLS, normalizing request framing, enforcing body-size ceilings and serving static assets, with the application server bound to an internal interface behind it.

**Why Not Code-Fixable:**
- Searched: docker-compose.yml, app/main.py, app/init_app.py
- Found: Uvicorn is published directly on port 8091 with --reload and a single worker; the application mounts its own static directory and no proxy service is defined.
- Missing: A reverse proxy service in the deployment topology, its configuration file, and the infrastructure decision about where TLS terminates.
- Conclusion: Introducing the front-end tier is a deployment-topology change involving new infrastructure components and certificate management, not an edit to this application's source.

**Recommended Action:** Platform engineering should add a hardened reverse proxy in front of the application, terminate TLS there, and move static asset delivery to it.

**Update (this run):** The repository-side portion of this guidance is now
implemented in `docker-compose.yml` and `deploy/nginx.conf`: an nginx front-end
terminates TLS (`listen 8443 ssl`, TLSv1.2/1.3, session tickets off), normalizes
request framing, enforces `client_max_body_size 1m`, and serves `/static/` from
its own mount so asset requests never reach the application process. The
application server publishes no host port and is reachable only on the internal
compose network.

Two items remain owned by platform engineering and are not verifiable from
repository files, which is why this stays Documented rather than Applied:

- **Certificate lifecycle.** `deploy/nginx.conf` references
  `/etc/nginx/tls/server.crt` and `server.key`, mounted from `${TLS_DIR}`.
  Issuance, renewal and rotation of that keypair are external.
- **Where TLS actually terminates in production.** The compose topology binds
  the proxy to `127.0.0.1:8443` for local use. If a cloud load balancer or
  service mesh terminates TLS instead, that decision and its configuration live
  outside this repository.

**Status:** Documented
