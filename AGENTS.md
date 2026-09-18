# Agent Instructions

<!-- SDE-SECURITY-HARDENING-START -->
## SD Elements Security Hardening

### Project Overview
| Field | Value |
|---|---|
| Application | dvra-clean-for-testing |
| SD Elements Project | https://staging.qa.sdelements.com/bunits/copilot-test/app/dvra-clean-for-testing |
| Project ID | 4552 |
| Total Countermeasures (Selected Scope) | 186 |
| Source | Codebase |

### Countermeasure Summary by Category
| Category | Count |
|---|---|
| CODE_FIX | 32 |
| ML_CODE | 0 |
| ML_DOC | 0 |
| PROCESS | 101 |
| INFRA | 53 |

### Domain: authentication
| ID | Title | Skill File | Priority | Category | Status | Source |
|---|---|---|---:|---|---|---|
| T2663 | Use a secure authentication mechanism for database connections | skills/authentication/T2663-use-a-secure-authentication-mechanism-fo/SKILL.md | 9 | CF | Applied | TEMPLATE |
| T2141 | Perform function level authorization in API | skills/authentication/T2141-python/SKILL.md | 8 | CF | Applied | LIBRARY:TA8555 |
| T2141 | Perform function level authorization in API | skills/authentication/T2141-javascript/SKILL.md | 8 | CF | Applied | LIBRARY:TA9345 |
| T29 | Use anti-Cross-Site Request Forgery (CSRF) tokens | skills/authentication/T29-python/SKILL.md | 7 | CF | Applied | LIBRARY:TA9301 |
| T1541 | Decide on the best CSRF defense for your application | skills/authentication/T1541-python/SKILL.md | 7 | CF | Applied | LIBRARY:TA9324 |
| T15 | Centralize authorization | skills/authentication/T15-centralize-authorization/SKILL.md | 9 | CF | Applied | TEMPLATE |
| T373 | Design and regulate access to unauthenticated parts of the application | skills/authentication/T373-design-and-regulate-access-to-unauthenti/SKILL.md | 8 | CF | Applied | TEMPLATE |
| T378 | Authorize every request for data objects | skills/authentication/T378-authorize-every-request-for-data-objects/SKILL.md | 8 | CF | Applied | TEMPLATE |
| T2652 | Consider adding plugins for stronger authentication protocols and stricter password complexity rules (MariaDB) | skills/authentication/T2652-consider-adding-plugins-for-stronger-aut/SKILL.md | 9 | CF | Documented | TEMPLATE |
| T18 | Make authorization decisions using full context | skills/authentication/T18-javascript/SKILL.md | 9 | CF | Applied | LIBRARY:TA9456 |
| T18 | Make authorization decisions using full context | skills/authentication/T18-python/SKILL.md | 9 | CF | Applied | LIBRARY:TA9505 |
| T1922 | Use secure OAuth 2.0 and OpenID Connect integration (where applicable) | skills/authentication/T1922-javascript/SKILL.md | 7 | CF | Documented | LIBRARY:TA9454 |
| T1922 | Use secure OAuth 2.0 and OpenID Connect integration (where applicable) | skills/authentication/T1922-python/SKILL.md | 7 | CF | Documented | LIBRARY:TA9523 |
| T66 | Prevent web pages from being loaded inside iFrame | skills/authentication/T66-prevent-web-pages-from-being-loaded-insi/SKILL.md | 7 | CF | Applied | TEMPLATE |
| T61 | Disable default accounts or change all default passwords | skills/authentication/T61-disable-default-accounts-or-change-all-d/SKILL.md | 9 | CF | Applied | TEMPLATE |
| T1365 | Mitigate Server Side Request Forgery | skills/authentication/T1365-javascript/SKILL.md | 8 | CF | Applied | LIBRARY:TA9284 |
| T1365 | Mitigate Server Side Request Forgery | skills/authentication/T1365-python/SKILL.md | 8 | CF | Applied | LIBRARY:TA8521 |
| T1887 | Decide on the right OAuth 2.0 flow for your application | skills/authentication/T1887-javascript/SKILL.md | 8 | CF | Documented | LIBRARY:TA9444 |
| T1887 | Decide on the right OAuth 2.0 flow for your application | skills/authentication/T1887-python/SKILL.md | 8 | CF | Documented | LIBRARY:TA9507 |
| T17 | Do not only rely on client-side authorization | skills/authentication/T17-python/SKILL.md | 8 | CF | Applied | LIBRARY:TA9296 |
| T17 | Do not only rely on client-side authorization | skills/authentication/T17-javascript/SKILL.md | 8 | CF | Applied | LIBRARY:TA9438 |
| T340 | Use an account and identity management system | skills/authentication/T340-use-an-account-and-identity-management-s/SKILL.md | 7 | CF | Applied | TEMPLATE |
| T76 | Do not hardcode passwords | skills/authentication/T76-javascript/SKILL.md | 10 | CF | Applied | LIBRARY:TA9291 |
| T76 | Do not hardcode passwords | skills/authentication/T76-python/SKILL.md | 10 | CF | Applied | LIBRARY:TA8509 |
| T2599 | Protect against connection string parameter pollution | skills/authentication/T2599-protect-against-connection-string-parame/SKILL.md | 9 | IN | Applied | TEMPLATE |
| T2615 | Limit network access by blocking connections from unknown IP addresses (PostgreSQL) | skills/authentication/T2615-limit-network-access-by-blocking-connect/SKILL.md | 8 | IN | Applied | TEMPLATE |
| T4601 | Prioritize static network configuration | skills/authentication/T4601-prioritize-static-network-configuration/SKILL.md | 8 | IN | Applied | TEMPLATE |
| T2616 | Use a secure authentication mechanism for database connections (PostgreSQL) | skills/authentication/T2616-use-a-secure-authentication-mechanism-fo/SKILL.md | 9 | IN | Documented | TEMPLATE |
| T2349 | Configure software to have secure settings by default | skills/authentication/T2349-configure-software-to-have-secure-settin/SKILL.md | 8 | IN | Applied | TEMPLATE |
| T2601 | Use Transparent Data Encryption with Enterprise Databases | skills/authentication/T2601-use-transparent-data-encryption-with-ent/SKILL.md | 8 | IN | Documented | TEMPLATE |
| T2662 | Restrict network access to the database server | skills/authentication/T2662-restrict-network-access-to-the-database/SKILL.md | 10 | IN | Applied | TEMPLATE |

### Domain: container-security
| ID | Title | Skill File | Priority | Category | Status | Source |
|---|---|---|---:|---|---|---|
| T37 | Avoid DOM-based Cross-Site Scripting (XSS) | skills/container-security/T37-javascript/SKILL.md | 8 | CF | Documented | LIBRARY:TA9334 |
| T37 | Avoid DOM-based Cross-Site Scripting (XSS) | skills/container-security/T37-python/SKILL.md | 8 | CF | Documented | LIBRARY:TA8540 |
| T1194 | Do not run SSH within containers (Docker) | skills/container-security/T1194-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8460 |
| T2115 | Enable image vulnerability scanning (Docker) | skills/container-security/T2115-enable-image-vulnerability-scanning-dock/SKILL.md | 7 | IN | Documented | TEMPLATE |
| T4746 | Ensure container images are secure | skills/container-security/T4746-ensure-container-images-are-secure/SKILL.md | 10 | IN | Applied | TEMPLATE |
| T1176 | Use trusted base images and include the latest security patches (Docker) | skills/container-security/T1176-docker/SKILL.md | 7 | IN | Applied | LIBRARY:TA8447 |
| T2105 | Enforce the use of client certificate bundles for unprivileged users to access UCP (Docker) | skills/container-security/T2105-enforce-the-use-of-client-certificate-bu/SKILL.md | 7 | IN | Documented | TEMPLATE |
| T2661 | Change insecure configuration defaults and remove unnecessary features | skills/container-security/T2661-change-insecure-configuration-defaults-a/SKILL.md | 9 | IN | Applied | TEMPLATE |
| T1190 | Restrict Linux Kernel Capabilities within containers (Docker) | skills/container-security/T1190-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8457 |
| T1144 | Prevent Server-Side Template Injection (SSTI) | skills/container-security/T1144-python/SKILL.md | 8 | IN | Documented | LIBRARY:TA9360 |
| T1174 | Create non-root users for containers (Docker) | skills/container-security/T1174-docker/SKILL.md | 9 | IN | Applied | LIBRARY:TA8448 |
| T1198 | Do not share the host's network namespace (Docker) | skills/container-security/T1198-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8456 |
| T1208 | Do not set mount propagation mode to 'shared' (Docker) | skills/container-security/T1208-docker/SKILL.md | 7 | IN | Applied | LIBRARY:TA8451 |
| T4748 | Implement Role-Based Access Control (RBAC) for container orchestration | skills/container-security/T4748-implement-role-based-access-control-rbac/SKILL.md | 10 | IN | Documented | TEMPLATE |
| T2257 | Regularly update and patch containerization systems | skills/container-security/T2257-regularly-update-and-patch-containerizat/SKILL.md | 10 | IN | Documented | TEMPLATE |
| T1156 | Do not use the aufs storage driver (Docker) | skills/container-security/T1156-docker/SKILL.md | 8 | IN | Documented | LIBRARY:TA8473 |
| T1158 | Configure TLS authentication for the Docker daemon (Docker) | skills/container-security/T1158-docker/SKILL.md | 8 | IN | Documented | LIBRARY:TA8472 |
| T2258 | Minimize host OS attack surface | skills/container-security/T2258-minimize-host-os-attack-surface/SKILL.md | 7 | IN | Documented | TEMPLATE |
| T4751 | Reduce the attack surface of container images | skills/container-security/T4751-reduce-the-attack-surface-of-container-i/SKILL.md | 10 | IN | Applied | TEMPLATE |
| T1196 | Open only needed ports on the containers (Docker) | skills/container-security/T1196-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8442 |
| T257 | Secure cross origin resource sharing (CORS) | skills/container-security/T257-javascript/SKILL.md | 8 | IN | Applied | LIBRARY:TA9481 |
| T257 | Secure cross origin resource sharing (CORS) | skills/container-security/T257-python/SKILL.md | 8 | IN | Applied | LIBRARY:TA9522 |
| T1172 | Secure daemon configuration files (Docker) | skills/container-security/T1172-secure-daemon-configuration-files-docker/SKILL.md | 8 | IN | Documented | TEMPLATE |
| T1188 | Configure Linux Security Modules (Docker) | skills/container-security/T1188-docker/SKILL.md | 8 | IN | Documented | LIBRARY:TA8458 |
| T1214 | Restrict containers from acquiring additional privileges (Docker) | skills/container-security/T1214-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8449 |
| T1186 | Do not store secrets in Dockerfiles (Docker) | skills/container-security/T1186-docker/SKILL.md | 10 | IN | Applied | LIBRARY:TA8441 |
| T7412 | Isolate dangerous functionality and risky third-party components using sandboxing or encapsulation | skills/container-security/T7412-isolate-dangerous-functionality-and-risk/SKILL.md | 9 | IN | Applied | TEMPLATE |
| T1204 | Mount container's root file system as read-only (Docker) | skills/container-security/T1204-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8453 |
| T2109 | Enable signed image enforcement (Docker) | skills/container-security/T2109-enable-signed-image-enforcement-docker/SKILL.md | 9 | IN | Documented | TEMPLATE |
| T1206 | Set the 'on-failure' container restart policy to 5 (Docker) | skills/container-security/T1206-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8452 |
| T1154 | Secure Docker registries (Docker) | skills/container-security/T1154-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8474 |
| T1166 | Encrypt data exchanged between containers on different nodes on the overlay network (Docker) | skills/container-security/T1166-docker/SKILL.md | 8 | IN | Documented | LIBRARY:TA8467 |
| T1150 | Configure container networks properly (Docker) | skills/container-security/T1150-docker/SKILL.md | 7 | IN | Applied | LIBRARY:TA8476 |
| T1212 | Confirm cgroup usage (Docker) | skills/container-security/T1212-docker/SKILL.md | 7 | IN | Applied | LIBRARY:TA8440 |
| T4750 | Isolate container networks | skills/container-security/T4750-isolate-container-networks/SKILL.md | 10 | IN | Applied | TEMPLATE |
| T1200 | Limit resources used by containers (Docker) | skills/container-security/T1200-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8455 |
| T4749 | Monitor containers in real-time | skills/container-security/T4749-monitor-containers-in-real-time/SKILL.md | 10 | IN | Documented | TEMPLATE |
| T1202 | Set container CPU priority appropriately (Docker) | skills/container-security/T1202-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8454 |
| T4747 | Limit container privileges | skills/container-security/T4747-limit-container-privileges/SKILL.md | 10 | IN | Applied | TEMPLATE |
| T1210 | Configure seccomp profile (Docker) | skills/container-security/T1210-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8450 |
| T1192 | Do not expose unnecessary host resources (Docker) | skills/container-security/T1192-docker/SKILL.md | 8 | IN | Applied | LIBRARY:TA8439 |

### Domain: cryptography
| ID | Title | Skill File | Priority | Category | Status | Source |
|---|---|---|---:|---|---|---|
| T2621 | Use file volume encryption and consider in-database encryption with pgcrypto (PostgreSQL) | skills/cryptography/T2621-use-file-volume-encryption-and-consider/SKILL.md | 8 | IN | Documented | TEMPLATE |
| T2620 | Protect data in transit with TLS (PostgreSQL) | skills/cryptography/T2620-protect-data-in-transit-with-tls-postgre/SKILL.md | 9 | IN | Documented | TEMPLATE |
| T2665 | Protect sensitive data at rest with encryption | skills/cryptography/T2665-protect-sensitive-data-at-rest-with-encr/SKILL.md | 8 | IN | Documented | TEMPLATE |
| T279 | Avoid dynamically loading any code without proper security considerations | skills/cryptography/T279-avoid-dynamically-loading-any-code-witho/SKILL.md | 8 | IN | Documented | TEMPLATE |
| T2666 | Protect data in transit with TLS (Database Server) | skills/cryptography/T2666-protect-data-in-transit-with-tls-databas/SKILL.md | 8 | IN | Documented | TEMPLATE |

### Domain: data-security
| ID | Title | Skill File | Priority | Category | Status | Source |
|---|---|---|---:|---|---|---|
| T2600 | Control the result set size returned by a query | skills/data-security/T2600-control-the-result-set-size-returned-by/SKILL.md | 7 | CF | Applied | TEMPLATE |
| T2598 | Implement query-level access control | skills/data-security/T2598-javascript/SKILL.md | 8 | CF | Applied | LIBRARY:TA9474 |
| T2598 | Implement query-level access control | skills/data-security/T2598-python/SKILL.md | 8 | CF | Applied | LIBRARY:TA9511 |
| T2139 | Prevent information exposure through APIs | skills/data-security/T2139-python/SKILL.md | 7 | CF | Applied | LIBRARY:TA9362 |
| T38 | Bind variables in SQL statements | skills/data-security/T38-python/SKILL.md | 10 | CF | Applied | LIBRARY:TA9283 |
| T2597 | Implement RBAC instead of individual accounts | skills/data-security/T2597-implement-rbac-instead-of-individual-acc/SKILL.md | 10 | CF | Applied | TEMPLATE |
| T2602 | Log typical database and server activities and related metadata | skills/data-security/T2602-log-typical-database-and-server-activiti/SKILL.md | 8 | CF | Applied | TEMPLATE |
| T186 | Use recommended settings and the latest patches for third party libraries and software | skills/data-security/T186-python/SKILL.md | 10 | CF | Applied | LIBRARY:TA9369 |
| T2605 | Validate database traffic | skills/data-security/T2605-validate-database-traffic/SKILL.md | 9 | IN | Documented | TEMPLATE |
| T2619 | Ensure that row-level security is correctly configured (PostgreSQL) | skills/data-security/T2619-ensure-that-row-level-security-is-correc/SKILL.md | 7 | IN | Documented | TEMPLATE |

### Domain: input-validation
| ID | Title | Skill File | Priority | Category | Status | Source |
|---|---|---|---:|---|---|---|
| T32 | Always perform input validation on a server | skills/input-validation/T32-python/SKILL.md | 7 | CF | Applied | LIBRARY:TA9302 |
| T7411 | Implement controls for content intended to be displayed as text | skills/input-validation/T7411-implement-controls-for-content-intended/SKILL.md | 7 | CF | Applied | TEMPLATE |
| T1542 | Use the correct HTTP methods for making state-changing operations | skills/input-validation/T1542-python/SKILL.md | 7 | CF | Applied | LIBRARY:TA9315 |
| T1542 | Use the correct HTTP methods for making state-changing operations | skills/input-validation/T1542-javascript/SKILL.md | 7 | CF | Applied | LIBRARY:TA9466 |
| T36 | Escape untrusted data in HTML, HTML attributes, CSS, and JavaScript | skills/input-validation/T36-python/SKILL.md | 8 | CF | Documented | LIBRARY:TA9293 |
| T36 | Escape untrusted data in HTML, HTML attributes, CSS, and JavaScript | skills/input-validation/T36-javascript/SKILL.md | 8 | CF | Documented | LIBRARY:TA8479 |
| T2348 | Perform code reviews | skills/input-validation/T2348-perform-code-reviews/SKILL.md | 8 | CF | Applied | TEMPLATE |
| T42 | Avoid relying on untrusted data for server-side selection | skills/input-validation/T42-javascript/SKILL.md | 10 | CF | Documented | LIBRARY:TA9458 |
| T42 | Avoid relying on untrusted data for server-side selection | skills/input-validation/T42-python/SKILL.md | 10 | CF | Documented | LIBRARY:TA9489 |
| T2603 | Protect backup archive bits | skills/input-validation/T2603-protect-backup-archive-bits/SKILL.md | 7 | CF | Documented | TEMPLATE |

### Domain: secure-coding
| ID | Title | Skill File | Priority | Category | Status | Source |
|---|---|---|---:|---|---|---|
| T4600 | Establish Out-of-Band Communications Channel | skills/secure-coding/T4600-establish-out-of-band-communications-cha/SKILL.md | 10 | IN | Documented | TEMPLATE |

### Progress Tracking
| Metric | Value |
|---|---|
| Expected Skill Files | 98 |
| Ledger Rows | 98 |

### Verification Checklist
- [x] PROCESS notes posted
- [x] Library lookup coverage complete
- [x] File generation verified
<!-- SDE-SECURITY-HARDENING-END -->
