#!/usr/bin/env python3
"""AI-authored content fields for the 68 template INFRA skill files.

Each entry supplies the `description` plus the Guidance / Why Not Code-Fixable
(searched, found, missing, conclusion) / Recommended Action fields that the
Documentation-only template format requires.
"""

INFRA = {

# ============================ api-security ============================

"T374": {
 "description": "Move HTTP request handling concerns such as TLS termination, compression, header normalization and static delivery onto a dedicated front-end module.",
 "guidance": "Dedicated, hardened modules should handle the protocol-level work rather than the application process: a reverse proxy terminating TLS, normalizing request framing, enforcing body-size ceilings and serving static assets, with the application server bound to an internal interface behind it.",
 "searched": "docker-compose.yml, app/main.py, app/init_app.py",
 "found": "Uvicorn is published directly on port 8091 with --reload and a single worker; the application mounts its own static directory and no proxy service is defined.",
 "missing": "A reverse proxy service in the deployment topology, its configuration file, and the infrastructure decision about where TLS terminates.",
 "conclusion": "Introducing the front-end tier is a deployment-topology change involving new infrastructure components and certificate management, not an edit to this application's source.",
 "action": "Platform engineering should add a hardened reverse proxy in front of the application, terminate TLS there, and move static asset delivery to it.",
},

# ============================ authentication ============================

"T1889": {
 "description": "Harden the configuration of the authorization server that issues tokens for this application.",
 "guidance": "The authorization server should pin its supported grant types and algorithms, register exact redirect URIs, disable implicit and resource-owner-password grants, enforce short access-token lifetimes with rotating refresh tokens, and publish its keys through a rotating JWKS endpoint.",
 "searched": "app/apis/auth/, app/config.py, pyproject.toml",
 "found": "The application signs its own HS256 tokens in app/apis/auth/utils/utils.py; there is no external authorization server and no OAuth client configuration.",
 "missing": "An identity provider to configure, its client registrations, and the operational ownership of its settings.",
 "conclusion": "There is no authorization server in this deployment to configure; the requirement applies to an identity platform that would be adopted at the architecture level.",
 "action": "The identity and access management team should own the authorization server configuration baseline if and when this service federates authentication.",
},

"T1918": {
 "description": "Federate authentication to the organization's single sign-on provider instead of holding local credentials.",
 "guidance": "Authentication should be delegated to the corporate identity provider over OIDC, with the application consuming validated identity assertions, mapping provider groups to its roles, and retaining no local password store.",
 "searched": "app/apis/auth/, app/init.py, app/db/models.py",
 "found": "The service maintains its own users table with locally hashed passwords and issues its own tokens; no identity provider integration exists.",
 "missing": "A tenant in the identity provider, client registration, group-to-role mapping and a migration plan for existing local accounts.",
 "conclusion": "SSO adoption is an organizational identity decision requiring provider onboarding and a credential migration, well beyond a change in this repository.",
 "action": "The identity and access management team should decide on SSO adoption and provide the client registration this service would consume.",
},

"T2277": {
 "description": "Confirm that accounts and identities for this service are managed through the organization's identity management system.",
 "guidance": "Verification means showing that account creation, modification and deprovisioning for this service flow through the central identity system, with joiner-mover-leaver events reflected automatically and periodic access reviews recorded.",
 "searched": "app/init.py, app/apis/auth/services/register_user_service.py, app/apis/users/",
 "found": "Accounts are created locally by the seeding routine and the public /register endpoint; there is no connection to a central identity system to verify.",
 "missing": "The identity management system integration itself, plus access-review evidence and deprovisioning records.",
 "conclusion": "The verification has no target until identity management is adopted; it is an audit activity against a platform this deployment does not yet use.",
 "action": "The identity and access management team should perform this verification once accounts for the service are sourced from the central identity system.",
},

"T340": {
 "description": "Source accounts and identities for this service from a central account and identity management system.",
 "guidance": "Identity lifecycle should be owned centrally: provisioning, role assignment, recertification and deprovisioning driven by the identity system rather than by application-local records.",
 "searched": "app/init.py, app/db/models.py, app/apis/auth/",
 "found": "A local users table is the sole identity store, seeded at startup and extended through self-registration.",
 "missing": "A central identity platform, a provisioning connector and an authoritative source for role assignment.",
 "conclusion": "Adopting central identity management is a platform decision requiring systems outside this repository.",
 "action": "The identity and access management team should own selection and rollout of the account and identity management system.",
},

# ============================ authorization ============================

"T2105": {
 "description": "Require client certificate bundles for unprivileged users accessing the container orchestration control plane.",
 "guidance": "Access to the orchestration control plane should be authenticated with per-user client certificate bundles that carry the user's role, with short validity periods and revocation, so control-plane access is never granted by a shared credential.",
 "searched": "docker-compose.yml, Dockerfile, start_app.sh, stop_app.sh",
 "found": "The deployment is a local Docker Compose stack; there is no UCP or equivalent orchestration control plane in the repository.",
 "missing": "An orchestration control plane, its user directory and a certificate authority issuing the bundles.",
 "conclusion": "There is no control plane in this deployment to configure; the control belongs to the container platform that would host the service.",
 "action": "The container platform team should enforce client certificate bundles on the orchestration control plane.",
},

"T2106": {
 "description": "Verify that client certificate bundles are actually required for unprivileged control-plane access.",
 "guidance": "Verification means attempting control-plane access without a bundle and confirming it is refused, and confirming that issued bundles carry the correct role and expiry.",
 "searched": "docker-compose.yml, Dockerfile, start_app.sh, stop_app.sh",
 "found": "No orchestration control plane is present in this deployment.",
 "missing": "The control plane and its access logs against which the verification would be performed.",
 "conclusion": "The verification cannot be performed without the platform it targets.",
 "action": "The container platform team should perform this verification on the orchestration control plane.",
},

"T2597": {
 "description": "Grant access through roles rather than through individually managed accounts.",
 "guidance": "Permissions should attach to a small set of roles that reflect job functions, with users receiving access solely by role membership, so entitlements can be reviewed and revoked as a set.",
 "searched": "app/db/models.py, app/apis/auth/utils/roles_based_auth_checker.py, docker-compose.yml",
 "found": "The application itself already models three roles; the gap is at the infrastructure layer, where database and host access use shared individual accounts such as the `admin` PostgreSQL user.",
 "missing": "Role definitions in the database and host platforms, and a directory to attach them to.",
 "conclusion": "Infrastructure-level role-based access control is configured in the database server and host platform, not in this repository's source.",
 "action": "The platform and database administration teams should define infrastructure roles and retire shared individual accounts.",
},

"T2606": {
 "description": "Verify that infrastructure access is granted by role rather than by individual account.",
 "guidance": "Verification means enumerating the accounts on the database and host platforms, confirming each maps to a role rather than a person or a shared secret, and producing a current entitlement report.",
 "searched": "docker-compose.yml, app/config.py, app/db/session.py",
 "found": "A single shared PostgreSQL account, `admin`, is used for all application access.",
 "missing": "Role definitions to verify against and an entitlement reporting mechanism.",
 "conclusion": "The verification depends on infrastructure role definitions that do not yet exist and are managed outside this repository.",
 "action": "The database administration team should produce the entitlement report once roles are defined.",
},

"T2607": {
 "description": "Verify that access control is enforced at the query level in the database.",
 "guidance": "Verification means confirming the database enforces per-row or per-view restrictions independently of the application, by connecting as a restricted role and observing that it cannot read rows outside its scope.",
 "searched": "app/db/models.py, app/db/session.py, app/migrations/versions/",
 "found": "All access uses one privileged database account; no row-level security policies or restricted views are defined in the migrations.",
 "missing": "Database roles, row-level security policies and the migration that would create them.",
 "conclusion": "Query-level access control is configured in the database server; there is no policy in this repository to verify.",
 "action": "The database administration team should define and verify query-level access controls.",
},

"T4748": {
 "description": "Implement role-based access control for the container orchestration platform.",
 "guidance": "Orchestration permissions should be granted through roles bound to groups, with separate roles for deploy, read and administrative operations, and no standing cluster-administrator access.",
 "searched": "docker-compose.yml, start_app.sh, stop_app.sh",
 "found": "Deployment is driven by shell scripts invoking Docker Compose on the host; anyone with Docker socket access has full control.",
 "missing": "An orchestration platform with an authorization model, and a directory to bind roles to.",
 "conclusion": "There is no orchestration authorization layer in this deployment to configure.",
 "action": "The container platform team should implement orchestration RBAC when the service is deployed to a managed platform.",
},

# ============================ ci-cd-security ============================

"T3903": {
 "description": "Apply the platform's application and webhook security controls to this repository.",
 "guidance": "Installed applications should be limited to those reviewed and needed, granted least-privilege scopes; webhooks should use a strong shared secret, deliver only over HTTPS, and have their payload signatures verified by every receiver.",
 "searched": "Repository root, .github/ (absent), docker-compose.yml",
 "found": "The repository contains no .github directory, no workflow definitions and no webhook receivers.",
 "missing": "The source-control platform's organization and repository settings, which are not represented as files in the repository.",
 "conclusion": "Application installations and webhook configuration live in the hosting platform's settings, not in versioned repository content.",
 "action": "The repository administrators should review installed applications and webhook configuration in the platform settings.",
},

"T3905": {
 "description": "Configure the build pipeline for secure and efficient execution.",
 "guidance": "Pipelines should pin third-party actions by commit SHA, scope tokens to the minimum permissions, avoid running untrusted pull-request code with secrets in scope, and cache only non-sensitive content with keys that cannot be poisoned.",
 "searched": "Repository root, .github/workflows/ (absent)",
 "found": "No pipeline definition exists in the repository.",
 "missing": "The workflow files themselves plus the platform-level runner and secret settings.",
 "conclusion": "There is no pipeline definition here to harden; creating one and configuring the platform is a CI/CD ownership decision.",
 "action": "The CI/CD owners should create the pipeline and apply the hardening baseline when build automation is introduced.",
},

"T3906": {
 "description": "Manage build workers securely.",
 "guidance": "Build workers should be ephemeral, isolated per job, run with least privilege, have no standing access to production credentials, and be rebuilt from a known-good image rather than reused across jobs.",
 "searched": "Repository root, .github/ (absent), Dockerfile, docker-compose.yml",
 "found": "No build automation is configured; images are built locally through Docker Compose.",
 "missing": "A build worker fleet and its provisioning configuration.",
 "conclusion": "Build worker management is an infrastructure concern owned by the CI/CD platform, with nothing in this repository to change.",
 "action": "The CI/CD platform team should define and own the build worker baseline.",
},

"T3907": {
 "description": "Define pipelines securely, with reviewed definitions and constrained triggers.",
 "guidance": "Pipeline definitions should be version-controlled and code-reviewed, triggers should exclude untrusted events from privileged workflows, and any deployment step should require an approval gate.",
 "searched": "Repository root, .github/workflows/ (absent)",
 "found": "No pipeline definition file exists.",
 "missing": "The pipeline definitions and the branch and environment protection settings that would constrain them.",
 "conclusion": "There is no definition in the repository to secure, and the protection settings live in the hosting platform.",
 "action": "The CI/CD owners should author the pipeline definitions under review and configure environment approvals.",
},

"T3908": {
 "description": "Sign the artifacts this project produces and require signatures downstream.",
 "guidance": "Every released artifact should be signed during the build, with signatures recorded in a transparency log, and consumers should verify the signature and provenance before deploying.",
 "searched": "Repository root, .github/ (absent), Dockerfile, pyproject.toml",
 "found": "There is no release or publishing process in the repository; images are built and run locally.",
 "missing": "A release pipeline, a signing identity and key custody arrangements.",
 "conclusion": "Artifact signing requires a release pipeline and key management that do not exist for this project.",
 "action": "The CI/CD owners should introduce signing as part of establishing a release process.",
},

"T3916": {
 "description": "Automate deployment so releases are reproducible and no person deploys by hand.",
 "guidance": "Deployment should run from a reviewed pipeline against an immutable artifact, with environment approvals, automatic rollback and a recorded audit trail, rather than from a developer workstation.",
 "searched": "start_app.sh, stop_app.sh, start_game.sh, docker-compose.yml",
 "found": "Deployment is a shell script that runs `docker compose up` on whatever host the operator is sitting at.",
 "missing": "A deployment pipeline, target environment definitions and release approval gates.",
 "conclusion": "Automating deployment requires CI/CD infrastructure and environment definitions that sit outside this repository.",
 "action": "The CI/CD owners should build the deployment pipeline and retire manual script-based deployment.",
},

"T3920": {
 "description": "Verify the application and webhook security controls on this repository.",
 "guidance": "Verification means reviewing the installed application list against the approved set, confirming each grant is least privilege, and confirming every webhook uses a secret and HTTPS with signature verification at the receiver.",
 "searched": "Repository root, .github/ (absent)",
 "found": "No webhook receivers or application manifests exist in the repository.",
 "missing": "Access to the hosting platform's settings, where installations and webhooks are configured.",
 "conclusion": "The evidence for this verification lives in platform settings rather than repository content.",
 "action": "The repository administrators should perform the review in the platform settings and record the outcome.",
},

"T3922": {
 "description": "Verify pipeline efficiency and security controls.",
 "guidance": "Verification means confirming actions are SHA-pinned, token permissions are minimal, untrusted code never runs with secrets in scope, and cache keys cannot be influenced by untrusted input.",
 "searched": "Repository root, .github/workflows/ (absent)",
 "found": "No pipeline exists to inspect.",
 "missing": "The pipeline definitions that would be the subject of the review.",
 "conclusion": "The verification has no subject until build automation is introduced.",
 "action": "The CI/CD owners should perform this review once pipelines exist.",
},

"T3923": {
 "description": "Verify that build workers are isolated, ephemeral and least-privileged.",
 "guidance": "Verification means confirming workers are destroyed after each job, do not share state, hold no standing production credentials, and are provisioned from a controlled image.",
 "searched": "Repository root, .github/ (absent)",
 "found": "No build worker fleet is associated with this repository.",
 "missing": "The worker fleet and its configuration.",
 "conclusion": "The verification targets infrastructure that does not exist for this project.",
 "action": "The CI/CD platform team should verify the worker baseline once build automation exists.",
},

"T3924": {
 "description": "Verify that pipeline definitions are reviewed and their triggers constrained.",
 "guidance": "Verification means confirming every pipeline definition is under code review, privileged workflows are not triggered by untrusted events, and deployment steps require approval.",
 "searched": "Repository root, .github/workflows/ (absent)",
 "found": "No pipeline definitions exist.",
 "missing": "The definitions and the branch and environment protection settings.",
 "conclusion": "There is nothing in the repository to verify, and protection settings are platform configuration.",
 "action": "The CI/CD owners should verify definitions and protections once pipelines are authored.",
},

"T3925": {
 "description": "Verify that released artifacts are signed and that signatures are checked before deployment.",
 "guidance": "Verification means taking a released artifact, confirming its signature validates against the expected identity, and confirming the deployment path rejects an unsigned artifact.",
 "searched": "Repository root, .github/ (absent), Dockerfile",
 "found": "No release process or signed artifact exists.",
 "missing": "A release pipeline producing signed artifacts.",
 "conclusion": "The verification cannot be performed without a release process.",
 "action": "The CI/CD owners should verify signing once a release process is in place.",
},

"T3933": {
 "description": "Verify that deployment is automated, approved and auditable.",
 "guidance": "Verification means confirming deployments originate from the pipeline against an immutable artifact, carry an approval record, and can be traced to a specific commit.",
 "searched": "start_app.sh, stop_app.sh, docker-compose.yml",
 "found": "Deployment is manual and leaves no audit record beyond local shell history.",
 "missing": "A deployment pipeline producing the records that would be verified.",
 "conclusion": "There is no automated deployment path to verify.",
 "action": "The CI/CD owners should verify the deployment process once it is automated.",
},

# ============================ container-security ============================

"T1155": {
 "description": "Verify that the container registries this project uses are reachable only over TLS with validated trust.",
 "guidance": "Verification means confirming no insecure-registry setting is present on any daemon that builds or runs these images, that registry endpoints are HTTPS, and that the registry CA is installed on the host.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "Images come from Docker Hub by implicit reference; the daemon configuration that governs registry trust is not part of the repository.",
 "missing": "Access to the Docker daemon configuration on the build and runtime hosts.",
 "conclusion": "Registry trust is configured on the Docker daemon and host, outside any file in this repository.",
 "action": "The platform team should verify daemon registry settings on the build and runtime hosts.",
},

"T1157": {
 "description": "Verify that the aufs storage driver is not in use on hosts running these containers.",
 "guidance": "Verification means inspecting the Docker daemon's active storage driver and confirming it is overlay2 or another supported driver rather than aufs.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "The storage driver is a daemon-level setting; nothing in the repository selects or references it.",
 "missing": "Access to the host's Docker daemon configuration and `docker info` output.",
 "conclusion": "Storage driver selection is host daemon configuration that no repository change can influence.",
 "action": "The platform team should confirm the storage driver on each container host.",
},

"T1159": {
 "description": "Verify that TLS client authentication is configured for the Docker daemon.",
 "guidance": "Verification means confirming the daemon listens only on a TLS socket with client certificate verification enabled, and that an unauthenticated connection to the daemon is refused.",
 "searched": "docker-compose.yml, start_app.sh, stop_app.sh",
 "found": "The scripts talk to the daemon over the local socket; daemon TLS settings are not represented in the repository.",
 "missing": "Access to the daemon's configuration and its certificate material.",
 "conclusion": "Daemon TLS is host configuration outside this repository's control.",
 "action": "The platform team should verify daemon TLS configuration on each container host.",
},

"T1172": {
 "description": "Secure the Docker daemon configuration files on the container hosts.",
 "guidance": "The daemon configuration, socket and certificate files should be owned by root, not writable by any other user, and audited for change, so nobody can alter daemon behaviour without detection.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh, stop_app.sh",
 "found": "No daemon configuration file is present in the repository.",
 "missing": "Filesystem access to the container hosts where those files live.",
 "conclusion": "Daemon file permissions are host hardening, not a change in application source.",
 "action": "The platform team should apply ownership and permission hardening to the daemon files.",
},

"T1173": {
 "description": "Verify that the Docker daemon configuration files are correctly secured.",
 "guidance": "Verification means checking ownership and mode on the daemon configuration, socket, service unit and certificate files against the expected baseline.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "The files in question are not part of the repository.",
 "missing": "Host filesystem access to inspect the daemon files.",
 "conclusion": "The verification is performed on the host, not against repository content.",
 "action": "The platform team should perform the file permission audit on each container host.",
},

"T1234": {
 "description": "Limit control of the Docker daemon to trusted users.",
 "guidance": "Membership of the docker group, or equivalent socket access, is equivalent to root on the host and should be restricted to a small, reviewed set of operators with access granted through a directory group rather than a local edit.",
 "searched": "docker-compose.yml, start_app.sh, stop_app.sh, Dockerfile",
 "found": "The scripts assume the invoking user already has daemon access; the repository does not control who has it.",
 "missing": "Host user and group membership, which is managed outside the repository.",
 "conclusion": "Daemon access control is host account management, not application configuration.",
 "action": "The platform team should review and restrict docker group membership on each host.",
},

"T1235": {
 "description": "Verify that only trusted users can control the Docker daemon.",
 "guidance": "Verification means enumerating the members of the docker group and the owners of the daemon socket, and confirming each is an approved operator.",
 "searched": "docker-compose.yml, start_app.sh, stop_app.sh",
 "found": "Group membership is not represented in the repository.",
 "missing": "Host account data needed for the enumeration.",
 "conclusion": "The verification is a host account review.",
 "action": "The platform team should enumerate and attest daemon access on each host.",
},

"T1236": {
 "description": "Audit the Docker daemon and its supporting files.",
 "guidance": "Host audit rules should record access to and modification of the daemon binary, socket, configuration and container storage directories, with the resulting records shipped to central log storage.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "No audit configuration exists in the repository.",
 "missing": "Host audit daemon rules and a log destination.",
 "conclusion": "Auditing the container runtime is host instrumentation applied outside this repository.",
 "action": "The platform team should add audit rules for the daemon and its files.",
},

"T1237": {
 "description": "Verify that the Docker daemon and its files are being audited.",
 "guidance": "Verification means confirming the audit rules are loaded, touching an audited path and observing the resulting record arrive in central log storage.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "No audit rules are defined in the repository.",
 "missing": "Access to the host audit configuration and the log pipeline.",
 "conclusion": "The verification is performed against host instrumentation.",
 "action": "The platform team should verify audit coverage on each container host.",
},

"T2109": {
 "description": "Require that only signed images may be pulled or run.",
 "guidance": "Content trust should be enforced at the daemon or admission layer so an unsigned image is refused, with signing keys held in a managed store and rotated.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "Images are referenced by floating tag with no signature requirement; enforcement is a daemon or platform setting.",
 "missing": "Daemon content-trust configuration or an admission controller, plus a signing key hierarchy.",
 "conclusion": "Signed-image enforcement is applied by the container platform, not by a file in this repository.",
 "action": "The container platform team should enable and enforce content trust.",
},

"T2110": {
 "description": "Verify that signed image enforcement is actually in effect.",
 "guidance": "Verification means attempting to run an unsigned image and confirming the platform refuses it, then confirming a signed image runs.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "No enforcement mechanism is configured, so the negative test would pass trivially.",
 "missing": "The enforcement layer that would be the subject of the test.",
 "conclusion": "The verification depends on platform enforcement that does not yet exist.",
 "action": "The container platform team should perform this verification after enabling content trust.",
},

"T2115": {
 "description": "Scan container images for known vulnerabilities before they are used.",
 "guidance": "Image scanning should run on every build and on a schedule for images already in the registry, with results gated by severity so a high-severity finding blocks promotion.",
 "searched": "Dockerfile, docker-compose.yml, .github/ (absent)",
 "found": "There is no build pipeline and no scanning step; images are built locally.",
 "missing": "A registry with scanning enabled and a pipeline to gate on the results.",
 "conclusion": "Scanning is enabled in the registry and pipeline platform rather than in this repository.",
 "action": "The container platform team should enable registry scanning and define the severity gate.",
},

"T2116": {
 "description": "Verify that image vulnerability scanning is enabled and gating.",
 "guidance": "Verification means confirming scan results exist for the current image, that they are recent, and that pushing an image with a high-severity finding is blocked.",
 "searched": "Dockerfile, docker-compose.yml, .github/ (absent)",
 "found": "No scan results are produced for this project.",
 "missing": "The scanning platform and its reports.",
 "conclusion": "The verification depends on a scanning service not yet in place.",
 "action": "The container platform team should verify scanning coverage once it is enabled.",
},

"T2256": {
 "description": "Authenticate and log every access to registries holding this project's images.",
 "guidance": "Registry access should require an identity, log every pull and push with the identity and image digest, and ship those records to central log storage for review.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "Images are pulled anonymously from a public registry; no private registry or access logging exists.",
 "missing": "A private registry with authentication and an audit log destination.",
 "conclusion": "Registry authentication and logging are properties of the registry service, configured outside this repository.",
 "action": "The container platform team should require authentication and enable access logging on the registry.",
},

"T2257": {
 "description": "Keep the container runtime and orchestration components patched.",
 "guidance": "The Docker engine, containerd, runc and the host kernel should be covered by a defined patch cadence with an emergency path for critical container-escape advisories.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "The repository pins application dependencies but has no influence over the container runtime version on the host.",
 "missing": "Host patch management policy and tooling.",
 "conclusion": "Runtime patching is host lifecycle management owned by the platform team.",
 "action": "The platform team should include the container runtime in the host patch cadence.",
},

"T4749": {
 "description": "Monitor running containers for anomalous behaviour in real time.",
 "guidance": "Runtime monitoring should observe process execution, network connections and file writes inside containers, alerting on behaviour that departs from the expected profile such as a shell spawning inside an application container.",
 "searched": "docker-compose.yml, app/init_app.py, Dockerfile",
 "found": "No runtime security agent, log shipping or alerting is configured for the containers.",
 "missing": "A runtime monitoring agent, its deployment and an alert destination.",
 "conclusion": "Runtime container monitoring is a security platform capability deployed alongside the workload, not code in this repository.",
 "action": "The security operations team should deploy runtime monitoring to the container hosts.",
},

# ============================ cryptography ============================

"T1167": {
 "description": "Verify that traffic between containers on different nodes is encrypted.",
 "guidance": "Verification means confirming the overlay network is created with encryption enabled and capturing inter-node traffic to confirm it is not readable in plaintext.",
 "searched": "docker-compose.yml, start_app.sh",
 "found": "The deployment is single-host Compose with no overlay network, so there is no cross-node traffic in this configuration.",
 "missing": "A multi-node cluster and its overlay network configuration.",
 "conclusion": "The verification applies to a clustered deployment that this repository does not define.",
 "action": "The container platform team should verify overlay encryption if the service is deployed across nodes.",
},

"T2601": {
 "description": "Enable transparent data encryption on the database.",
 "guidance": "The database should encrypt its data files at rest using keys held in a managed key store, with rotation and separation between the key custodian and the database administrator.",
 "searched": "docker-compose.yml, app/db/session.py, app/config.py",
 "found": "PostgreSQL runs from the stock image with a plain volume; no encryption-at-rest configuration is present.",
 "missing": "Database server configuration, a key management service and the storage layer the volume lives on.",
 "conclusion": "Transparent data encryption is configured on the database server and storage platform, not in application source.",
 "action": "The database administration team should enable encryption at rest with managed keys.",
},

"T2603": {
 "description": "Protect database backup archives so a backup cannot become an easier path to the data.",
 "guidance": "Backups should be encrypted with keys distinct from the live database, stored with restricted access and integrity protection, and periodically test-restored.",
 "searched": "docker-compose.yml, start_app.sh, stop_app.sh, app/migrations/",
 "found": "No backup process is defined anywhere in the repository; the database volume is the only copy of the data.",
 "missing": "A backup process, its storage destination and key custody.",
 "conclusion": "Backup protection is an operational process defined outside this repository.",
 "action": "The database administration team should define encrypted, access-controlled backups with restore testing.",
},

"T2610": {
 "description": "Verify that transparent data encryption is in effect on the database.",
 "guidance": "Verification means confirming the encryption setting is active on the running instance and that raw data files do not reveal table contents.",
 "searched": "docker-compose.yml, app/db/session.py",
 "found": "No encryption at rest is configured, so there is nothing yet to verify.",
 "missing": "The database encryption configuration that would be the subject of the check.",
 "conclusion": "The verification depends on a database setting applied outside this repository.",
 "action": "The database administration team should verify encryption once it is enabled.",
},

"T2612": {
 "description": "Verify that backup archives are protected.",
 "guidance": "Verification means confirming backups are encrypted, that access to the backup store is restricted and logged, and that a restore has been exercised recently.",
 "searched": "docker-compose.yml, start_app.sh, stop_app.sh",
 "found": "No backup process exists to inspect.",
 "missing": "A backup process and its storage location.",
 "conclusion": "The verification has no subject until backups are defined.",
 "action": "The database administration team should verify backup protection once backups exist.",
},

"T2620": {
 "description": "Require TLS for client connections to PostgreSQL.",
 "guidance": "The server should be configured with a certificate and require SSL for all client connections, with clients verifying the server certificate against a known CA.",
 "searched": "docker-compose.yml, app/db/session.py, app/config.py",
 "found": "PostgreSQL runs with stock settings and the application connects with a URL carrying no sslmode; the server-side requirement is set in postgresql.conf and pg_hba.conf.",
 "missing": "Server configuration files and certificate material, neither of which is in the repository.",
 "conclusion": "Requiring TLS is a database server configuration change; the matching client-side change is tracked separately under the data-in-transit countermeasure.",
 "action": "The database administration team should issue a server certificate and require SSL in pg_hba.conf.",
},

"T2621": {
 "description": "Encrypt the database file volume and consider in-database encryption for the most sensitive columns.",
 "guidance": "The volume holding database files should be encrypted at the storage layer, with pgcrypto used selectively for columns that must stay unreadable even to someone with file access.",
 "searched": "docker-compose.yml, app/db/models.py, app/migrations/versions/",
 "found": "The `pg_volume` Docker volume is unencrypted and no pgcrypto extension is enabled in the migrations.",
 "missing": "Storage-layer encryption for the volume and a key management arrangement.",
 "conclusion": "Volume encryption is a storage platform capability configured outside this repository.",
 "action": "The platform and database administration teams should encrypt the database volume and select columns for pgcrypto.",
},

"T2665": {
 "description": "Encrypt sensitive data at rest across the systems that hold it.",
 "guidance": "Data classified as sensitive should be encrypted wherever it resides — database files, backups, log archives and object storage — with keys managed centrally and rotated.",
 "searched": "docker-compose.yml, app/db/models.py, app/config.py",
 "found": "The database volume, any log output and any backup copy are all unencrypted.",
 "missing": "Storage encryption across each of those layers plus a key management service.",
 "conclusion": "Encryption at rest spans storage platforms and key management, which are infrastructure concerns.",
 "action": "The platform team should apply encryption at rest to every store holding this service's data.",
},

"T2666": {
 "description": "Require TLS for all connections to the database server.",
 "guidance": "The database server should refuse plaintext connections outright, presenting a certificate issued by a known CA, so that no client can negotiate an unencrypted session.",
 "searched": "docker-compose.yml, app/db/session.py",
 "found": "The stock PostgreSQL image accepts plaintext connections and nothing in the deployment forbids them.",
 "missing": "Server-side pg_hba.conf entries and certificate material.",
 "conclusion": "Refusing plaintext is enforced by the database server configuration, outside this repository.",
 "action": "The database administration team should require hostssl entries and remove plaintext host entries.",
},

# ============================ database-security ============================

"T2602": {
 "description": "Log database and server activity with enough metadata to support investigation.",
 "guidance": "The database should log connections, disconnections, DDL, privilege changes and failed authentications with timestamps and source identity, shipped to storage the database administrators cannot silently alter.",
 "searched": "docker-compose.yml, app/db/session.py, app/migrations/",
 "found": "PostgreSQL runs with default logging and no log shipping; nothing in the repository configures it.",
 "missing": "postgresql.conf logging settings and a central log destination.",
 "conclusion": "Database activity logging is server configuration applied outside this repository.",
 "action": "The database administration team should enable activity logging and ship the records centrally.",
},

"T2605": {
 "description": "Validate and monitor database traffic for anomalous statements.",
 "guidance": "A database activity monitor or proxy should inspect statements for patterns such as injection attempts or bulk extraction, alerting on deviations from the application's normal query profile.",
 "searched": "app/db/session.py, docker-compose.yml",
 "found": "The application connects directly to PostgreSQL with no intermediary and no statement monitoring.",
 "missing": "A database activity monitoring component and its alert routing.",
 "conclusion": "Traffic validation is delivered by a monitoring appliance or proxy deployed alongside the database.",
 "action": "The database administration and security operations teams should deploy database activity monitoring.",
},

"T2611": {
 "description": "Verify that database and server activity is being logged with the required metadata.",
 "guidance": "Verification means confirming the logging settings are active, generating a representative event and observing it arrive in central storage with the expected fields.",
 "searched": "docker-compose.yml, app/db/session.py",
 "found": "No logging configuration or destination exists to verify.",
 "missing": "The database logging configuration and central log storage.",
 "conclusion": "The verification depends on server configuration outside this repository.",
 "action": "The database administration team should verify logging once it is configured.",
},

"T2614": {
 "description": "Verify that database traffic validation is operating.",
 "guidance": "Verification means issuing a representative anomalous statement and confirming the monitor detects and alerts on it.",
 "searched": "app/db/session.py, docker-compose.yml",
 "found": "No monitoring component is deployed.",
 "missing": "The monitoring component that would generate the detection.",
 "conclusion": "The verification cannot be performed without the monitoring layer.",
 "action": "The security operations team should verify detection once monitoring is deployed.",
},

"T2615": {
 "description": "Restrict which network sources may connect to PostgreSQL.",
 "guidance": "Host-based access rules should permit connections only from the application's address range, with everything else rejected, reinforced by network-level filtering.",
 "searched": "docker-compose.yml, app/db/session.py",
 "found": "The database is reachable from any container on the shared default network; access rules live in pg_hba.conf, which is not in the repository.",
 "missing": "pg_hba.conf and the network policy configuration.",
 "conclusion": "Source restriction is database server and network configuration applied outside this repository.",
 "action": "The database administration team should tighten pg_hba.conf and the surrounding network rules.",
},

"T2616": {
 "description": "Use a strong authentication mechanism for PostgreSQL connections.",
 "guidance": "The server should require scram-sha-256 or certificate authentication for every connection, with md5 and trust methods removed from the host-based configuration.",
 "searched": "docker-compose.yml, app/config.py, app/db/session.py",
 "found": "The application supplies a username and password; the accepted authentication method is decided by the server's pg_hba.conf, which is not part of the repository.",
 "missing": "pg_hba.conf and the server's password_encryption setting.",
 "conclusion": "The authentication mechanism is chosen in the database server configuration.",
 "action": "The database administration team should require scram-sha-256 and remove weaker methods.",
},

"T2619": {
 "description": "Configure row-level security policies on the tables holding user data.",
 "guidance": "Row-level security should be enabled on the user-scoped tables with policies that restrict each application role to the rows it owns, so a flaw in application code cannot expose another user's records.",
 "searched": "app/db/models.py, app/migrations/versions/",
 "found": "The migrations create tables with no row-level security, and the application connects as a single privileged role that any policy would bypass.",
 "missing": "Database roles for the application's identities and the migration that would enable and define the policies.",
 "conclusion": "Row-level security requires a database role model that the deployment does not have; it is a database design change owned by the database administrators.",
 "action": "The database administration team should define the role model and row-level security policies.",
},

"T2652": {
 "description": "Strengthen database authentication with plugins for stronger protocols and password complexity.",
 "guidance": "The database should enforce password complexity, expiry and reuse restrictions through its authentication plugins, or delegate authentication to a central directory.",
 "searched": "docker-compose.yml, app/config.py",
 "found": "The database uses a static password supplied through the compose environment; no complexity or expiry policy is applied.",
 "missing": "Server-side authentication plugin configuration.",
 "conclusion": "Authentication plugins are installed and configured on the database server.",
 "action": "The database administration team should enable password policy enforcement on the server.",
},

"T2661": {
 "description": "Change insecure database defaults and remove features the application does not use.",
 "guidance": "The server should be brought to a hardened baseline: default accounts removed, sample databases dropped, unused extensions and procedural languages disabled, and listen addresses narrowed.",
 "searched": "docker-compose.yml, app/migrations/versions/, app/db/session.py",
 "found": "The stock PostgreSQL image runs with default settings, a default superuser named `admin` and a fixed password from the compose file.",
 "missing": "A hardened server configuration and the baseline that defines it.",
 "conclusion": "Server hardening is applied to the database instance, not through application source.",
 "action": "The database administration team should apply the hardening baseline to the instance.",
},

"T2662": {
 "description": "Restrict network reachability of the database server.",
 "guidance": "The database should be reachable only from the application tier, on an internal network segment, never published to a host interface or the internet.",
 "searched": "docker-compose.yml",
 "found": "The database uses `expose` rather than a published port, which is sound, but it shares the default network with every other container and no internal-only network is declared.",
 "missing": "Network segmentation policy at the platform level beyond what Compose expresses.",
 "conclusion": "Meaningful network restriction is enforced by the platform's network policy; the compose-level change is tracked separately under the container network isolation countermeasure.",
 "action": "The platform team should place the database on an internal segment with explicit ingress rules.",
},

"T2663": {
 "description": "Use a secure authentication mechanism for database connections generally.",
 "guidance": "Connections should authenticate with scram-sha-256, client certificates or short-lived credentials issued by a secret store, rather than a static password shared between environments.",
 "searched": "app/config.py, app/db/session.py, docker-compose.yml",
 "found": "A static password is passed through the environment and used for every connection.",
 "missing": "A secret store capable of issuing short-lived database credentials, and server support for the chosen method.",
 "conclusion": "Moving to certificate or dynamically issued credentials requires infrastructure the deployment does not yet have.",
 "action": "The database administration and platform teams should select and roll out the stronger mechanism.",
},

# ============================ dependency-management ============================

"T3913": {
 "description": "Secure the package registry this project publishes to or consumes from.",
 "guidance": "Registry access should require authentication, publishing should be limited to the release pipeline, packages should be immutable once published, and upstream proxying should be restricted to reviewed sources.",
 "searched": "pyproject.toml, poetry.lock, Dockerfile, .github/ (absent)",
 "found": "Dependencies are resolved from the public index with no private registry, and the project publishes nothing.",
 "missing": "A private registry and its access configuration.",
 "conclusion": "Registry security settings live in the registry service rather than in this repository.",
 "action": "The platform team should configure the package registry controls if a private registry is adopted.",
},

"T3930": {
 "description": "Verify the package registry security controls.",
 "guidance": "Verification means confirming anonymous publish is refused, that package versions are immutable, and that upstream proxying is limited to approved sources.",
 "searched": "pyproject.toml, poetry.lock, .github/ (absent)",
 "found": "No private registry is associated with this project.",
 "missing": "The registry that would be the subject of the verification.",
 "conclusion": "The verification has no subject in the current setup.",
 "action": "The platform team should verify registry controls once a private registry exists.",
},

# ============================ infrastructure-hardening ============================

"T2258": {
 "description": "Minimize the attack surface of the hosts running this service.",
 "guidance": "Container hosts should run a minimal operating system with unused services disabled, unnecessary packages removed, local firewalling enabled and remote access limited to a bastion path.",
 "searched": "Dockerfile, docker-compose.yml, start_app.sh",
 "found": "The repository defines the container image but nothing about the host operating system it runs on.",
 "missing": "Host build configuration and a hardening baseline.",
 "conclusion": "Host hardening is applied to the machine image, outside this repository. The equivalent work inside the container image is tracked separately under the image attack-surface countermeasure.",
 "action": "The platform team should apply the host hardening baseline to the container hosts.",
},

"T4601": {
 "description": "Prefer static, declared network configuration over dynamically discovered addressing.",
 "guidance": "Addresses, subnets and routes for the service tier should be declared and version-controlled, so connectivity does not depend on runtime discovery that an attacker could influence.",
 "searched": "docker-compose.yml, app/config.py",
 "found": "Container addressing is left entirely to Docker's default bridge with no declared subnet, and the application resolves the database by the service name `db`.",
 "missing": "A declared network topology at the platform level, including subnets and address assignment.",
 "conclusion": "Network addressing policy is defined by the platform that hosts the containers rather than by this repository.",
 "action": "The platform team should declare the network topology and addressing for the service tier.",
},

# ============================ input-validation ============================

"T573": {
 "description": "Prevent spoofing of service registry entries used for service discovery.",
 "guidance": "Where a service registry is used, its entries should be authenticated and integrity-protected, and consumers should validate the identity of a discovered endpoint before contacting it.",
 "searched": "app/apis/, app/config.py, pyproject.toml, docker-compose.yml",
 "found": "The service exposes a REST API and discovers nothing through a registry; there is no UDDI, ebXML or equivalent directory in the stack.",
 "missing": "A service registry, which this architecture does not use.",
 "conclusion": "The countermeasure targets a service discovery mechanism that is not part of this application.",
 "action": "The architecture owners should confirm the registry remains out of scope, and revisit if service discovery is introduced.",
},

"T576": {
 "description": "Verify that service registry spoofing is prevented.",
 "guidance": "Verification means attempting to publish or alter a registry entry without authorization and confirming the attempt is refused, then confirming consumers reject an unverified endpoint.",
 "searched": "app/apis/, app/config.py, docker-compose.yml",
 "found": "No service registry is present in the deployment.",
 "missing": "The registry that would be the subject of the test.",
 "conclusion": "The verification has no subject in this architecture.",
 "action": "The architecture owners should record the countermeasure as not applicable unless service discovery is adopted.",
},

# ============================ logging-monitoring ============================

"T349": {
 "description": "Protect audit records from unauthorized access and modification.",
 "guidance": "Audit records should be shipped off the generating host promptly, stored append-only with restricted read access, retained for the required period and monitored for gaps that would indicate tampering.",
 "searched": "app/init_app.py, docker-compose.yml, Dockerfile",
 "found": "The application writes no audit log today and the containers have no log shipping configured, so there is no protected store to speak of.",
 "missing": "Central log storage with access control, retention and integrity protection.",
 "conclusion": "Protecting audit records requires log infrastructure outside this repository; producing the records is tracked separately under the structured audit logging countermeasure.",
 "action": "The security operations team should provide access-controlled, append-only log storage for this service.",
},

"T350": {
 "description": "Verify that audit information is sufficiently protected.",
 "guidance": "Verification means confirming that only authorized roles can read the audit store, that records cannot be modified or deleted before their retention period, and that an attempt to do so is itself recorded.",
 "searched": "app/init_app.py, docker-compose.yml",
 "found": "No audit records and no log store exist to inspect.",
 "missing": "The log storage platform that would be the subject of the verification.",
 "conclusion": "The verification depends on log infrastructure that is not yet in place.",
 "action": "The security operations team should verify the protections once central log storage is provisioned.",
},

# ============================ secrets-management ============================

"T214": {
 "description": "Protect confidential files on the operating system and server hosting this service.",
 "guidance": "Files holding credentials, keys or sensitive data should be owned by the service account, unreadable by other users, stored on encrypted media, and excluded from images and backups that travel more widely.",
 "searched": "Dockerfile, docker-compose.yml, app/config.py, start_app.sh",
 "found": "Configuration is loaded from a `.env` file resolved relative to the working directory and the compose file carries credentials inline, but the repository sets no ownership or mode on any of it.",
 "missing": "Host filesystem permissions, a secret mount arrangement and encrypted storage for the host.",
 "conclusion": "File protection is applied on the host and through the secret delivery mechanism, not through application source. The related code change — removing in-code secret defaults — is tracked separately.",
 "action": "The platform team should deliver secrets through restricted-permission secret mounts on encrypted storage.",
},

}
