<!-- SDE-SECURITY-HARDENING-START -->

# Security Hardening — SD Elements

## Project Overview

| Field | Value |
|-------|-------|
| Application | MCP-194.2 |
| SD Elements project | https://staging.qa.sdelements.com/bunits/1101/projects/4560/ |
| Project ID | 4560 |
| Total Countermeasures | 293 (selected scope) |
| Source | Codebase |
| Repository path | /Users/isilveira/dvra-clean-for-testing |

## Countermeasure Summary by Category

| Category | Count | Handling |
|----------|-------|----------|
| CODE_FIX | 203 | Skill file with a code fix |
| INFRA | 73 | Documentation-only skill file |
| PROCESS | 17 | Noted in SD Elements, no skill file |
| **File-tracked total** | **276** | **276 skill files** (71 library-sourced, 205 template) |

## Countermeasure Index

One row per skill file. A countermeasure with library content for several technologies has one row per technology.

### api-security (39 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T7357 | Drive request parsing with strict Pydantic models and forbid extra fields (FastAPI) | [skills/api-security/T7357-drive-request-parsing-with-strict-pydantic-model/SKILL.md](skills/api-security/T7357-drive-request-parsing-with-strict-pydantic-model/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7362 | Enforce trusted hosts and HTTPS-only transport with Starlette middleware (FastAPI) | [skills/api-security/T7362-enforce-trusted-hosts-and-https-only-transport-w/SKILL.md](skills/api-security/T7362-enforce-trusted-hosts-and-https-only-transport-w/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7365 | Rate-limit authentication and expensive endpoints (FastAPI) | [skills/api-security/T7365-rate-limit-authentication-and-expensive-endpoint/SKILL.md](skills/api-security/T7365-rate-limit-authentication-and-expensive-endpoint/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7373 | Trust forwarded headers only from known proxies behind TLS (FastAPI) | [skills/api-security/T7373-trust-forwarded-headers-only-from-known-proxies/SKILL.md](skills/api-security/T7373-trust-forwarded-headers-only-from-known-proxies/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7376 | Add automated security regression tests for critical controls (FastAPI) | [skills/api-security/T7376-add-automated-security-regression-tests-for-crit/SKILL.md](skills/api-security/T7376-add-automated-security-regression-tests-for-crit/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7379 | Serve static files only from a dedicated non-sensitive directory (FastAPI) | [skills/api-security/T7379-serve-static-files-only-from-a-dedicated-non-sen/SKILL.md](skills/api-security/T7379-serve-static-files-only-from-a-dedicated-non-sen/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T228 | Test that application restricts HTTP message size | [skills/api-security/T228-test-that-application-restricts-http-message-siz/SKILL.md](skills/api-security/T228-test-that-application-restricts-http-message-siz/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T2596 | Prevent HTTP Request Smuggling | [skills/api-security/T2596-prevent-http-request-smuggling/SKILL.md](skills/api-security/T2596-prevent-http-request-smuggling/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T35 | Fine-tune HTTP server settings | [skills/api-security/T35-fine-tune-http-server-settings/SKILL.md](skills/api-security/T35-fine-tune-http-server-settings/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T7358 | Constrain responses with response_model to prevent sensitive-data exposure (FastAPI) | [skills/api-security/T7358-constrain-responses-with-response-model-to-preve/SKILL.md](skills/api-security/T7358-constrain-responses-with-response-model-to-preve/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T1362 | Perform message throttling in Web APIs | [skills/api-security/T1362-python/SKILL.md](skills/api-security/T1362-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9329 |
| T1363 | Verify if message throttling is properly performed in Web APIs | [skills/api-security/T1363-verify-if-message-throttling-is-properly-perform/SKILL.md](skills/api-security/T1363-verify-if-message-throttling-is-properly-perform/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T257 | Secure cross origin resource sharing (CORS) | [skills/api-security/T257-python/SKILL.md](skills/api-security/T257-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9522 |
| T318 | Verify security of cross origin resource sharing (CORS) | [skills/api-security/T318-verify-security-of-cross-origin-resource-sharing/SKILL.md](skills/api-security/T318-verify-security-of-cross-origin-resource-sharing/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T536 | Restrict the size of incoming messages in services | [skills/api-security/T536-restrict-the-size-of-incoming-messages-in-servic/SKILL.md](skills/api-security/T536-restrict-the-size-of-incoming-messages-in-servic/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T537 | Test that the size of incoming messages in services is restricted | [skills/api-security/T537-test-that-the-size-of-incoming-messages-in-servi/SKILL.md](skills/api-security/T537-test-that-the-size-of-incoming-messages-in-servi/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T7361 | Configure CORS with explicit origins and never wildcard with credentials (FastAPI) | [skills/api-security/T7361-configure-cors-with-explicit-origins-and-never-w/SKILL.md](skills/api-security/T7361-configure-cors-with-explicit-origins-and-never-w/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T7363 | Add security response headers via middleware (FastAPI) | [skills/api-security/T7363-add-security-response-headers-via-middleware-fas/SKILL.md](skills/api-security/T7363-add-security-response-headers-via-middleware-fas/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T7364 | Enforce request-body and upload size limits to resist memory-exhaustion DoS (FastAPI) | [skills/api-security/T7364-enforce-request-body-and-upload-size-limits-to-r/SKILL.md](skills/api-security/T7364-enforce-request-body-and-upload-size-limits-to-r/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T7375 | Keep blocking work off the async event loop (FastAPI) | [skills/api-security/T7375-keep-blocking-work-off-the-async-event-loop-fast/SKILL.md](skills/api-security/T7375-keep-blocking-work-off-the-async-event-loop-fast/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T116 | Test for regular expression denial of service | [skills/api-security/T116-test-for-regular-expression-denial-of-service/SKILL.md](skills/api-security/T116-test-for-regular-expression-denial-of-service/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T119 | Test for clickjacking | [skills/api-security/T119-test-for-clickjacking/SKILL.md](skills/api-security/T119-test-for-clickjacking/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T1541 | Decide on the best CSRF defense for your application | [skills/api-security/T1541-python/SKILL.md](skills/api-security/T1541-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9324 |
| T1542 | Use the correct HTTP methods for making state-changing operations | [skills/api-security/T1542-python/SKILL.md](skills/api-security/T1542-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9315 |
| T166 | Protect against JSON hijacking | [skills/api-security/T166-python/SKILL.md](skills/api-security/T166-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9317 |
| T167 | Test that the application is not vulnerable to JSON Hijacking | [skills/api-security/T167-test-that-the-application-is-not-vulnerable-to-j/SKILL.md](skills/api-security/T167-test-that-the-application-is-not-vulnerable-to-j/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2139 | Prevent information exposure through APIs | [skills/api-security/T2139-python/SKILL.md](skills/api-security/T2139-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9362 |
| T2140 | Test that APIs do not expose sensitive information | [skills/api-security/T2140-test-that-apis-do-not-expose-sensitive-informati/SKILL.md](skills/api-security/T2140-test-that-apis-do-not-expose-sensitive-informati/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2600 | Control the result set size returned by a query | [skills/api-security/T2600-control-the-result-set-size-returned-by-a-query/SKILL.md](skills/api-security/T2600-control-the-result-set-size-returned-by-a-query/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2609 | Verify that the result set size returned by queries are controlled | [skills/api-security/T2609-python/SKILL.md](skills/api-security/T2609-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8583 |
| T29 | Use anti-Cross-Site Request Forgery (CSRF) tokens | [skills/api-security/T29-python/SKILL.md](skills/api-security/T29-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9301 |
| T374 | Offload HTTP request handling to dedicated modules | [skills/api-security/T374-offload-http-request-handling-to-dedicated-modul/SKILL.md](skills/api-security/T374-offload-http-request-handling-to-dedicated-modul/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T66 | Prevent web pages from being loaded inside iFrame | [skills/api-security/T66-prevent-web-pages-from-being-loaded-inside-ifram/SKILL.md](skills/api-security/T66-prevent-web-pages-from-being-loaded-inside-ifram/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T7368 | Protect cookie-authenticated routes with SameSite cookies and CSRF tokens (FastAPI) | [skills/api-security/T7368-protect-cookie-authenticated-routes-with-samesit/SKILL.md](skills/api-security/T7368-protect-cookie-authenticated-routes-with-samesit/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T7370 | Return generic errors and disable debug output in production (FastAPI) | [skills/api-security/T7370-return-generic-errors-and-disable-debug-output-i/SKILL.md](skills/api-security/T7370-return-generic-errors-and-disable-debug-output-i/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T7372 | Restrict interactive API documentation exposure in production (FastAPI) | [skills/api-security/T7372-restrict-interactive-api-documentation-exposure/SKILL.md](skills/api-security/T7372-restrict-interactive-api-documentation-exposure/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T7382 | Make critical state-changing operations replay-resistant (FastAPI) | [skills/api-security/T7382-make-critical-state-changing-operations-replay-r/SKILL.md](skills/api-security/T7382-make-critical-state-changing-operations-replay-r/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T75 | Use regular expressions that are not vulnerable to Denial of Service | [skills/api-security/T75-python/SKILL.md](skills/api-security/T75-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9350 |
| T96 | Test if your site is vulnerable to CSRF | [skills/api-security/T96-test-if-your-site-is-vulnerable-to-csrf/SKILL.md](skills/api-security/T96-test-if-your-site-is-vulnerable-to-csrf/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |

### authentication (31 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T7354 | Hash user passwords with Argon2 or bcrypt via a vetted library (FastAPI) | [skills/authentication/T7354-hash-user-passwords-with-argon2-or-bcrypt-via-a/SKILL.md](skills/authentication/T7354-hash-user-passwords-with-argon2-or-bcrypt-via-a/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T1918 | Integrate with SSO | [skills/authentication/T1918-integrate-with-sso/SKILL.md](skills/authentication/T1918-integrate-with-sso/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T1919 | Use JSON Web Token (JWT) securely | [skills/authentication/T1919-python/SKILL.md](skills/authentication/T1919-python/SKILL.md) | 9 | CODE_FIX | Applied | LIBRARY:TA9313 |
| T20 | Generate unique session IDs and reset old IDs after authentication | [skills/authentication/T20-python/SKILL.md](skills/authentication/T20-python/SKILL.md) | 9 | CODE_FIX | Applied | LIBRARY:TA9297 |
| T323 | Test that default accounts are disabled or default passwords are changed | [skills/authentication/T323-test-that-default-accounts-are-disabled-or-defau/SKILL.md](skills/authentication/T323-test-that-default-accounts-are-disabled-or-defau/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T558 | Authenticate all other components before any network communication with them | [skills/authentication/T558-authenticate-all-other-components-before-any-net/SKILL.md](skills/authentication/T558-authenticate-all-other-components-before-any-net/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T589 | Verify that all the components are authenticated explicitly | [skills/authentication/T589-verify-that-all-the-components-are-authenticated/SKILL.md](skills/authentication/T589-verify-that-all-the-components-are-authenticated/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T61 | Disable default accounts or change all default passwords | [skills/authentication/T61-disable-default-accounts-or-change-all-default-p/SKILL.md](skills/authentication/T61-disable-default-accounts-or-change-all-default-p/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T7353 | Authenticate requests with signed JWTs and explicitly pinned algorithms (FastAPI) | [skills/authentication/T7353-authenticate-requests-with-signed-jwts-and-expli/SKILL.md](skills/authentication/T7353-authenticate-requests-with-signed-jwts-and-expli/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T7367 | Validate the Origin and authenticate every WebSocket handshake (FastAPI) | [skills/authentication/T7367-validate-the-origin-and-authenticate-every-webso/SKILL.md](skills/authentication/T7367-validate-the-origin-and-authenticate-every-webso/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T78 | Test strength of password reset mechanism | [skills/authentication/T78-test-strength-of-password-reset-mechanism/SKILL.md](skills/authentication/T78-test-strength-of-password-reset-mechanism/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T86 | Test session ID uniqueness and rotation after authentication | [skills/authentication/T86-test-session-id-uniqueness-and-rotation-after-au/SKILL.md](skills/authentication/T86-test-session-id-uniqueness-and-rotation-after-au/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T114 | Test system-to-system authentication lockout or throttling | [skills/authentication/T114-test-system-to-system-authentication-lockout-or/SKILL.md](skills/authentication/T114-test-system-to-system-authentication-lockout-or/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1539 | Clear browser data on user logout | [skills/authentication/T1539-clear-browser-data-on-user-logout/SKILL.md](skills/authentication/T1539-clear-browser-data-on-user-logout/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1540 | Verify that browser data is cleared upon user logout | [skills/authentication/T1540-verify-that-browser-data-is-cleared-upon-user-lo/SKILL.md](skills/authentication/T1540-verify-that-browser-data-is-cleared-upon-user-lo/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1887 | Decide on the right OAuth 2.0 flow for your application | [skills/authentication/T1887-python/SKILL.md](skills/authentication/T1887-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9507 |
| T230 | Test that server-to-server system accounts meet minimum password requirements | [skills/authentication/T230-test-that-server-to-server-system-accounts-meet/SKILL.md](skills/authentication/T230-test-that-server-to-server-system-accounts-meet/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4439 | Prevent authentication attacks (Bash/Shell) | [skills/authentication/T4439-prevent-authentication-attacks-bash-shell/SKILL.md](skills/authentication/T4439-prevent-authentication-attacks-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4450 | Test authentication (Bash/Shell) | [skills/authentication/T4450-test-authentication-bash-shell/SKILL.md](skills/authentication/T4450-test-authentication-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T69 | Strong password requirements for server-to-server system accounts | [skills/authentication/T69-python/SKILL.md](skills/authentication/T69-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8615 |
| T70 | Implement account lockout or authentication throttling for system accounts | [skills/authentication/T70-python/SKILL.md](skills/authentication/T70-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9493 |
| T1889 | Secure the configuration of the authorization server | [skills/authentication/T1889-secure-the-configuration-of-the-authorization-se/SKILL.md](skills/authentication/T1889-secure-the-configuration-of-the-authorization-se/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T1922 | Use secure OAuth 2.0 and OpenID Connect integration (where applicable) | [skills/authentication/T1922-python/SKILL.md](skills/authentication/T1922-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9523 |
| T2276 | Test to confirm that authorization and authentication controls are in place for access to resources | [skills/authentication/T2276-test-to-confirm-that-authorization-and-authentic/SKILL.md](skills/authentication/T2276-test-to-confirm-that-authorization-and-authentic/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2277 | Test to confirm the use of an account and identity management system | [skills/authentication/T2277-test-to-confirm-the-use-of-an-account-and-identi/SKILL.md](skills/authentication/T2277-test-to-confirm-the-use-of-an-account-and-identi/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T338 | Control access to resources through user authentication and authorization | [skills/authentication/T338-python/SKILL.md](skills/authentication/T338-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9312 |
| T340 | Use an account and identity management system | [skills/authentication/T340-use-an-account-and-identity-management-system/SKILL.md](skills/authentication/T340-use-an-account-and-identity-management-system/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T394 | Secure one-time passwords (OTP) | [skills/authentication/T394-python/SKILL.md](skills/authentication/T394-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9351 |
| T395 | Verify that one-time passwords (OTP) are securely used | [skills/authentication/T395-verify-that-one-time-passwords-otp-are-securely/SKILL.md](skills/authentication/T395-verify-that-one-time-passwords-otp-are-securely/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T406 | Secure symmetric-key authentication | [skills/authentication/T406-secure-symmetric-key-authentication/SKILL.md](skills/authentication/T406-secure-symmetric-key-authentication/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T407 | Verify that symmetric-key authentication is secure | [skills/authentication/T407-verify-that-symmetric-key-authentication-is-secu/SKILL.md](skills/authentication/T407-verify-that-symmetric-key-authentication-is-secu/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |

### authorization (25 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T2597 | Implement RBAC instead of individual accounts | [skills/authorization/T2597-implement-rbac-instead-of-individual-accounts/SKILL.md](skills/authorization/T2597-implement-rbac-instead-of-individual-accounts/SKILL.md) | 10 | INFRA | Documented | TEMPLATE |
| T2606 | Verify RBAC implemented instead of individual accounts | [skills/authorization/T2606-verify-rbac-implemented-instead-of-individual-ac/SKILL.md](skills/authorization/T2606-verify-rbac-implemented-instead-of-individual-ac/SKILL.md) | 10 | INFRA | Documented | TEMPLATE |
| T4748 | Implement Role-Based Access Control (RBAC) for container orchestration | [skills/authorization/T4748-implement-role-based-access-control-rbac-for-con/SKILL.md](skills/authorization/T4748-implement-role-based-access-control-rbac-for-con/SKILL.md) | 10 | INFRA | Documented | TEMPLATE |
| T7355 | Enforce endpoint authorization with dependencies and OAuth2 scopes (FastAPI) | [skills/authorization/T7355-enforce-endpoint-authorization-with-dependencies/SKILL.md](skills/authorization/T7355-enforce-endpoint-authorization-with-dependencies/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T15 | Centralize authorization | [skills/authorization/T15-centralize-authorization/SKILL.md](skills/authorization/T15-centralize-authorization/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T18 | Make authorization decisions using full context | [skills/authorization/T18-python/SKILL.md](skills/authorization/T18-python/SKILL.md) | 9 | CODE_FIX | Applied | LIBRARY:TA9505 |
| T184 | Perform authorization checks on RESTful web services | [skills/authorization/T184-python/SKILL.md](skills/authorization/T184-python/SKILL.md) | 9 | CODE_FIX | Applied | LIBRARY:TA9310 |
| T226 | Verify that authorization is centralized | [skills/authorization/T226-verify-that-authorization-is-centralized/SKILL.md](skills/authorization/T226-verify-that-authorization-is-centralized/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T106 | Test that site is not vulnerable to direct object access attacks | [skills/authorization/T106-test-that-site-is-not-vulnerable-to-direct-objec/SKILL.md](skills/authorization/T106-test-that-site-is-not-vulnerable-to-direct-objec/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T128 | Test for access control bypass through user-controlled keys | [skills/authorization/T128-test-for-access-control-bypass-through-user-cont/SKILL.md](skills/authorization/T128-test-for-access-control-bypass-through-user-cont/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T17 | Do not only rely on client-side authorization | [skills/authorization/T17-python/SKILL.md](skills/authorization/T17-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9296 |
| T2141 | Perform function level authorization in API | [skills/authorization/T2141-python/SKILL.md](skills/authorization/T2141-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8555 |
| T2142 | Verify that function level authorization is implemented in API | [skills/authorization/T2142-python/SKILL.md](skills/authorization/T2142-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9512 |
| T2282 | Test to confirm that unauthenticated parts of the application are accessible | [skills/authorization/T2282-test-to-confirm-that-unauthenticated-parts-of-th/SKILL.md](skills/authorization/T2282-test-to-confirm-that-unauthenticated-parts-of-th/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T2598 | Implement query-level access control | [skills/authorization/T2598-python/SKILL.md](skills/authorization/T2598-python/SKILL.md) | 8 | INFRA | Documented | LIBRARY:TA9511 |
| T2607 | Verify query-level access control is implemented | [skills/authorization/T2607-verify-query-level-access-control-is-implemented/SKILL.md](skills/authorization/T2607-verify-query-level-access-control-is-implemented/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T373 | Design and regulate access to unauthenticated parts of the application | [skills/authorization/T373-design-and-regulate-access-to-unauthenticated-pa/SKILL.md](skills/authorization/T373-design-and-regulate-access-to-unauthenticated-pa/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T378 | Authorize every request for data objects | [skills/authorization/T378-authorize-every-request-for-data-objects/SKILL.md](skills/authorization/T378-authorize-every-request-for-data-objects/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4440 | Enforce access controls (Bash/Shell) | [skills/authorization/T4440-enforce-access-controls-bash-shell/SKILL.md](skills/authorization/T4440-enforce-access-controls-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4451 | Test access controls (Bash/Shell) | [skills/authorization/T4451-test-access-controls-bash-shell/SKILL.md](skills/authorization/T4451-test-access-controls-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T50 | Use indirect object reference maps if accessing files | [skills/authorization/T50-python/SKILL.md](skills/authorization/T50-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9304 |
| T7356 | Enforce object-level ownership checks on every resource access (FastAPI) | [skills/authorization/T7356-enforce-object-level-ownership-checks-on-every-r/SKILL.md](skills/authorization/T7356-enforce-object-level-ownership-checks-on-every-r/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T85 | Test server-side enforcement of authorization | [skills/authorization/T85-test-server-side-enforcement-of-authorization/SKILL.md](skills/authorization/T85-test-server-side-enforcement-of-authorization/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T2105 | Enforce the use of client certificate bundles for unprivileged users to access UCP (Docker) | [skills/authorization/T2105-enforce-the-use-of-client-certificate-bundles-fo/SKILL.md](skills/authorization/T2105-enforce-the-use-of-client-certificate-bundles-fo/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T2106 | Verify that the use of client certificate bundles for unprivileged users is enforced (Docker) | [skills/authorization/T2106-verify-that-the-use-of-client-certificate-bundle/SKILL.md](skills/authorization/T2106-verify-that-the-use-of-client-certificate-bundle/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |

### ci-cd-security (14 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T3903 | Implement application and webhook security strategies (GitHub) | [skills/ci-cd-security/T3903-implement-application-and-webhook-security-strat/SKILL.md](skills/ci-cd-security/T3903-implement-application-and-webhook-security-strat/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3905 | Ensure pipeline efficiency and security (GitHub) | [skills/ci-cd-security/T3905-ensure-pipeline-efficiency-and-security-github/SKILL.md](skills/ci-cd-security/T3905-ensure-pipeline-efficiency-and-security-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3906 | Implement secure build worker management (GitHub) | [skills/ci-cd-security/T3906-implement-secure-build-worker-management-github/SKILL.md](skills/ci-cd-security/T3906-implement-secure-build-worker-management-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3907 | Ensure pipeline definition and security (GitHub) | [skills/ci-cd-security/T3907-ensure-pipeline-definition-and-security-github/SKILL.md](skills/ci-cd-security/T3907-ensure-pipeline-definition-and-security-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3908 | Enforce artifact signing (GitHub) | [skills/ci-cd-security/T3908-enforce-artifact-signing-github/SKILL.md](skills/ci-cd-security/T3908-enforce-artifact-signing-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3915 | Enforce separation of deployment configuration files (GitHub) | [skills/ci-cd-security/T3915-enforce-separation-of-deployment-configuration-f/SKILL.md](skills/ci-cd-security/T3915-enforce-separation-of-deployment-configuration-f/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T3916 | Ensure automated and secure deployment (GitHub) | [skills/ci-cd-security/T3916-ensure-automated-and-secure-deployment-github/SKILL.md](skills/ci-cd-security/T3916-ensure-automated-and-secure-deployment-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3920 | Test application and webhook security strategies (GitHub) | [skills/ci-cd-security/T3920-test-application-and-webhook-security-strategies/SKILL.md](skills/ci-cd-security/T3920-test-application-and-webhook-security-strategies/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3922 | Test pipeline efficiency and security (GitHub) | [skills/ci-cd-security/T3922-test-pipeline-efficiency-and-security-github/SKILL.md](skills/ci-cd-security/T3922-test-pipeline-efficiency-and-security-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3923 | Test secure build worker management (GitHub) | [skills/ci-cd-security/T3923-test-secure-build-worker-management-github/SKILL.md](skills/ci-cd-security/T3923-test-secure-build-worker-management-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3924 | Test pipeline definition and security (GitHub) | [skills/ci-cd-security/T3924-test-pipeline-definition-and-security-github/SKILL.md](skills/ci-cd-security/T3924-test-pipeline-definition-and-security-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3925 | Test artifact signing (GitHub) | [skills/ci-cd-security/T3925-test-artifact-signing-github/SKILL.md](skills/ci-cd-security/T3925-test-artifact-signing-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3932 | Test separation of deployment configuration files (GitHub) | [skills/ci-cd-security/T3932-test-separation-of-deployment-configuration-file/SKILL.md](skills/ci-cd-security/T3932-test-separation-of-deployment-configuration-file/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T3933 | Test automated and secure deployment (GitHub) | [skills/ci-cd-security/T3933-test-automated-and-secure-deployment-github/SKILL.md](skills/ci-cd-security/T3933-test-automated-and-secure-deployment-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |

### container-security (58 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T1917 | Perform container security assessment | [skills/container-security/T1917-perform-container-security-assessment/SKILL.md](skills/container-security/T1917-perform-container-security-assessment/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T2257 | Regularly update and patch containerization systems | [skills/container-security/T2257-regularly-update-and-patch-containerization-syst/SKILL.md](skills/container-security/T2257-regularly-update-and-patch-containerization-syst/SKILL.md) | 10 | INFRA | Documented | TEMPLATE |
| T4746 | Ensure container images are secure | [skills/container-security/T4746-ensure-container-images-are-secure/SKILL.md](skills/container-security/T4746-ensure-container-images-are-secure/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T4747 | Limit container privileges | [skills/container-security/T4747-limit-container-privileges/SKILL.md](skills/container-security/T4747-limit-container-privileges/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T4749 | Monitor containers in real-time | [skills/container-security/T4749-monitor-containers-in-real-time/SKILL.md](skills/container-security/T4749-monitor-containers-in-real-time/SKILL.md) | 10 | INFRA | Documented | TEMPLATE |
| T4750 | Isolate container networks | [skills/container-security/T4750-isolate-container-networks/SKILL.md](skills/container-security/T4750-isolate-container-networks/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T4751 | Reduce the attack surface of container images | [skills/container-security/T4751-reduce-the-attack-surface-of-container-images/SKILL.md](skills/container-security/T4751-reduce-the-attack-surface-of-container-images/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T1174 | Create non-root users for containers (Docker) | [skills/container-security/T1174-docker/SKILL.md](skills/container-security/T1174-docker/SKILL.md) | 9 | CODE_FIX | Applied | LIBRARY:TA8448 |
| T1175 | Verify that containers are not run as root (Docker) | [skills/container-security/T1175-verify-that-containers-are-not-run-as-root-docke/SKILL.md](skills/container-security/T1175-verify-that-containers-are-not-run-as-root-docke/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T2109 | Enable signed image enforcement (Docker) | [skills/container-security/T2109-enable-signed-image-enforcement-docker/SKILL.md](skills/container-security/T2109-enable-signed-image-enforcement-docker/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2110 | Verify that signed image enforcement is enabled (Docker) | [skills/container-security/T2110-verify-that-signed-image-enforcement-is-enabled/SKILL.md](skills/container-security/T2110-verify-that-signed-image-enforcement-is-enabled/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T1154 | Secure Docker registries (Docker) | [skills/container-security/T1154-docker/SKILL.md](skills/container-security/T1154-docker/SKILL.md) | 8 | INFRA | Documented | LIBRARY:TA8474 |
| T1155 | Verify that Docker registries are secure (Docker) | [skills/container-security/T1155-verify-that-docker-registries-are-secure-docker/SKILL.md](skills/container-security/T1155-verify-that-docker-registries-are-secure-docker/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1156 | Do not use the aufs storage driver (Docker) | [skills/container-security/T1156-docker/SKILL.md](skills/container-security/T1156-docker/SKILL.md) | 8 | INFRA | Documented | LIBRARY:TA8473 |
| T1157 | Verify that the aufs storage driver is not used (Docker) | [skills/container-security/T1157-verify-that-the-aufs-storage-driver-is-not-used/SKILL.md](skills/container-security/T1157-verify-that-the-aufs-storage-driver-is-not-used/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1158 | Configure TLS authentication for the Docker daemon (Docker) | [skills/container-security/T1158-docker/SKILL.md](skills/container-security/T1158-docker/SKILL.md) | 8 | INFRA | Documented | LIBRARY:TA8472 |
| T1159 | Verify that TLS authentication is configured for the Docker daemon (Docker) | [skills/container-security/T1159-verify-that-tls-authentication-is-configured-for/SKILL.md](skills/container-security/T1159-verify-that-tls-authentication-is-configured-for/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1172 | Secure daemon configuration files (Docker) | [skills/container-security/T1172-secure-daemon-configuration-files-docker/SKILL.md](skills/container-security/T1172-secure-daemon-configuration-files-docker/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1173 | Verify that daemon configuration files are secured (Docker) | [skills/container-security/T1173-verify-that-daemon-configuration-files-are-secur/SKILL.md](skills/container-security/T1173-verify-that-daemon-configuration-files-are-secur/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1188 | Configure Linux Security Modules (Docker) | [skills/container-security/T1188-docker/SKILL.md](skills/container-security/T1188-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8458 |
| T1189 | Test if Linux Security Modules are securely configured (Docker) | [skills/container-security/T1189-docker/SKILL.md](skills/container-security/T1189-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8462 |
| T1190 | Restrict Linux Kernel Capabilities within containers (Docker) | [skills/container-security/T1190-docker/SKILL.md](skills/container-security/T1190-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8457 |
| T1191 | Test if Linux Kernel Capabilities are restricted within containers (Docker) | [skills/container-security/T1191-docker/SKILL.md](skills/container-security/T1191-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8461 |
| T1192 | Do not expose unnecessary host resources (Docker) | [skills/container-security/T1192-docker/SKILL.md](skills/container-security/T1192-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8439 |
| T1193 | Test if unnecessary host resources are exposed (Docker) | [skills/container-security/T1193-test-if-unnecessary-host-resources-are-exposed-d/SKILL.md](skills/container-security/T1193-test-if-unnecessary-host-resources-are-exposed-d/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1194 | Do not run SSH within containers (Docker) | [skills/container-security/T1194-docker/SKILL.md](skills/container-security/T1194-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8460 |
| T1195 | Test if SSH is running within containers (Docker) | [skills/container-security/T1195-test-if-ssh-is-running-within-containers-docker/SKILL.md](skills/container-security/T1195-test-if-ssh-is-running-within-containers-docker/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1196 | Open only needed ports on the containers (Docker) | [skills/container-security/T1196-docker/SKILL.md](skills/container-security/T1196-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8442 |
| T1197 | Test if only needed ports are open on the containers (Docker) | [skills/container-security/T1197-test-if-only-needed-ports-are-open-on-the-contai/SKILL.md](skills/container-security/T1197-test-if-only-needed-ports-are-open-on-the-contai/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1198 | Do not share the host's network namespace (Docker) | [skills/container-security/T1198-docker/SKILL.md](skills/container-security/T1198-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8456 |
| T1199 | Test that the host's network namespace is not shared (Docker) | [skills/container-security/T1199-test-that-the-host-s-network-namespace-is-not-sh/SKILL.md](skills/container-security/T1199-test-that-the-host-s-network-namespace-is-not-sh/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1200 | Limit resources used by containers (Docker) | [skills/container-security/T1200-docker/SKILL.md](skills/container-security/T1200-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8455 |
| T1201 | Test that resources used by containers are limited (Docker) | [skills/container-security/T1201-test-that-resources-used-by-containers-are-limit/SKILL.md](skills/container-security/T1201-test-that-resources-used-by-containers-are-limit/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1202 | Set container CPU priority appropriately (Docker) | [skills/container-security/T1202-docker/SKILL.md](skills/container-security/T1202-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8454 |
| T1203 | Test if container CPU priority is appropriately set (Docker) | [skills/container-security/T1203-test-if-container-cpu-priority-is-appropriately/SKILL.md](skills/container-security/T1203-test-if-container-cpu-priority-is-appropriately/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1204 | Mount container's root file system as read-only (Docker) | [skills/container-security/T1204-docker/SKILL.md](skills/container-security/T1204-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8453 |
| T1205 | Test if the container's root file system is mounted as read-only (Docker) | [skills/container-security/T1205-test-if-the-container-s-root-file-system-is-moun/SKILL.md](skills/container-security/T1205-test-if-the-container-s-root-file-system-is-moun/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1206 | Set the 'on-failure' container restart policy to 5 (Docker) | [skills/container-security/T1206-docker/SKILL.md](skills/container-security/T1206-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8452 |
| T1207 | Test that the 'on-failure' container restart policy is set to 5 (Docker) | [skills/container-security/T1207-test-that-the-on-failure-container-restart-polic/SKILL.md](skills/container-security/T1207-test-that-the-on-failure-container-restart-polic/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1210 | Configure seccomp profile (Docker) | [skills/container-security/T1210-docker/SKILL.md](skills/container-security/T1210-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8450 |
| T1211 | Verify that seccomp profile is enabled (Docker) | [skills/container-security/T1211-verify-that-seccomp-profile-is-enabled-docker/SKILL.md](skills/container-security/T1211-verify-that-seccomp-profile-is-enabled-docker/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1214 | Restrict containers from acquiring additional privileges (Docker) | [skills/container-security/T1214-docker/SKILL.md](skills/container-security/T1214-docker/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8449 |
| T1215 | Verify that containers are restricted from acquiring additional privileges (Docker) | [skills/container-security/T1215-verify-that-containers-are-restricted-from-acqui/SKILL.md](skills/container-security/T1215-verify-that-containers-are-restricted-from-acqui/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1234 | Only allow trusted users to control the Docker daemon (Docker) | [skills/container-security/T1234-only-allow-trusted-users-to-control-the-docker-d/SKILL.md](skills/container-security/T1234-only-allow-trusted-users-to-control-the-docker-d/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1235 | Test that only trusted users can control the Docker daemon (Docker) | [skills/container-security/T1235-test-that-only-trusted-users-can-control-the-doc/SKILL.md](skills/container-security/T1235-test-that-only-trusted-users-can-control-the-doc/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1236 | Audit the Docker daemon and its files (Docker) | [skills/container-security/T1236-audit-the-docker-daemon-and-its-files-docker/SKILL.md](skills/container-security/T1236-audit-the-docker-daemon-and-its-files-docker/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1237 | Test that the Docker daemon and its files are audited (Docker) | [skills/container-security/T1237-test-that-the-docker-daemon-and-its-files-are-au/SKILL.md](skills/container-security/T1237-test-that-the-docker-daemon-and-its-files-are-au/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2256 | Authenticate and log all access to registries containing sensitive or proprietary images | [skills/container-security/T2256-authenticate-and-log-all-access-to-registries-co/SKILL.md](skills/container-security/T2256-authenticate-and-log-all-access-to-registries-co/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T1150 | Configure container networks properly (Docker) | [skills/container-security/T1150-docker/SKILL.md](skills/container-security/T1150-docker/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8476 |
| T1151 | Verify that container networks are configured properly (Docker) | [skills/container-security/T1151-docker/SKILL.md](skills/container-security/T1151-docker/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8469 |
| T1176 | Use trusted base images and include the latest security patches (Docker) | [skills/container-security/T1176-docker/SKILL.md](skills/container-security/T1176-docker/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8447 |
| T1177 | Verify that secure and updated images are used (Docker) | [skills/container-security/T1177-docker/SKILL.md](skills/container-security/T1177-docker/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8477 |
| T1208 | Do not set mount propagation mode to 'shared' (Docker) | [skills/container-security/T1208-docker/SKILL.md](skills/container-security/T1208-docker/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8451 |
| T1209 | Verify that mount propagation mode is not set to 'shared' (Docker) | [skills/container-security/T1209-verify-that-mount-propagation-mode-is-not-set-to/SKILL.md](skills/container-security/T1209-verify-that-mount-propagation-mode-is-not-set-to/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T1212 | Confirm cgroup usage (Docker) | [skills/container-security/T1212-docker/SKILL.md](skills/container-security/T1212-docker/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8440 |
| T1213 | Verify that cgroup usage is confirmed (Docker) | [skills/container-security/T1213-verify-that-cgroup-usage-is-confirmed-docker/SKILL.md](skills/container-security/T1213-verify-that-cgroup-usage-is-confirmed-docker/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2115 | Enable image vulnerability scanning (Docker) | [skills/container-security/T2115-enable-image-vulnerability-scanning-docker/SKILL.md](skills/container-security/T2115-enable-image-vulnerability-scanning-docker/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T2116 | Verify that image vulnerability scanning is enabled (Docker) | [skills/container-security/T2116-verify-that-image-vulnerability-scanning-is-enab/SKILL.md](skills/container-security/T2116-verify-that-image-vulnerability-scanning-is-enab/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |

### cryptography (29 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T1468 | Encrypt sensitive data at rest in the browser | [skills/cryptography/T1468-encrypt-sensitive-data-at-rest-in-the-browser/SKILL.md](skills/cryptography/T1468-encrypt-sensitive-data-at-rest-in-the-browser/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T197 | Validate the signature of all remote code/updates to verify their origin and integrity | [skills/cryptography/T197-validate-the-signature-of-all-remote-code-update/SKILL.md](skills/cryptography/T197-validate-the-signature-of-all-remote-code-update/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T2485 | Verify that remote code and updates are correctly encrypted and signed (server side) | [skills/cryptography/T2485-verify-that-remote-code-and-updates-are-correctl/SKILL.md](skills/cryptography/T2485-verify-that-remote-code-and-updates-are-correctl/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T2486 | Encrypt and sign all remote code/updates (server side) | [skills/cryptography/T2486-encrypt-and-sign-all-remote-code-updates-server/SKILL.md](skills/cryptography/T2486-encrypt-and-sign-all-remote-code-updates-server/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T2620 | Protect data in transit with TLS (PostgreSQL) | [skills/cryptography/T2620-protect-data-in-transit-with-tls-postgresql/SKILL.md](skills/cryptography/T2620-protect-data-in-transit-with-tls-postgresql/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T439 | Verify that the origin and integrity of remote code and updates are checked (client side) | [skills/cryptography/T439-verify-that-the-origin-and-integrity-of-remote-c/SKILL.md](skills/cryptography/T439-verify-that-the-origin-and-integrity-of-remote-c/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T1166 | Encrypt data exchanged between containers on different nodes on the overlay network (Docker) | [skills/cryptography/T1166-docker/SKILL.md](skills/cryptography/T1166-docker/SKILL.md) | 8 | INFRA | Documented | LIBRARY:TA8467 |
| T1167 | Verify that data exchanged between containers on different nodes on the overlay network is encrypted (Docker) | [skills/cryptography/T1167-verify-that-data-exchanged-between-containers-on/SKILL.md](skills/cryptography/T1167-verify-that-data-exchanged-between-containers-on/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T21 | Ensure all data in transit is encrypted using a secure TLS channel | [skills/cryptography/T21-python/SKILL.md](skills/cryptography/T21-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8620 |
| T2601 | Use Transparent Data Encryption with Enterprise Databases | [skills/cryptography/T2601-use-transparent-data-encryption-with-enterprise/SKILL.md](skills/cryptography/T2601-use-transparent-data-encryption-with-enterprise/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2610 | Verify that Transparent Data Encryption is utilized with Enterprise Databases | [skills/cryptography/T2610-verify-that-transparent-data-encryption-is-utili/SKILL.md](skills/cryptography/T2610-verify-that-transparent-data-encryption-is-utili/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2621 | Use file volume encryption and consider in-database encryption with pgcrypto (PostgreSQL) | [skills/cryptography/T2621-use-file-volume-encryption-and-consider-in-datab/SKILL.md](skills/cryptography/T2621-use-file-volume-encryption-and-consider-in-datab/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2665 | Protect sensitive data at rest with encryption | [skills/cryptography/T2665-protect-sensitive-data-at-rest-with-encryption/SKILL.md](skills/cryptography/T2665-protect-sensitive-data-at-rest-with-encryption/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2666 | Protect data in transit with TLS (Database Server) | [skills/cryptography/T2666-protect-data-in-transit-with-tls-database-server/SKILL.md](skills/cryptography/T2666-protect-data-in-transit-with-tls-database-server/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T4443 | Prevent cryptographic failures (Bash/Shell) | [skills/cryptography/T4443-prevent-cryptographic-failures-bash-shell/SKILL.md](skills/cryptography/T4443-prevent-cryptographic-failures-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T445 | Verify that only approved cryptographic algorithms and key lengths are used | [skills/cryptography/T445-verify-that-only-approved-cryptographic-algorith/SKILL.md](skills/cryptography/T445-verify-that-only-approved-cryptographic-algorith/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4454 | Test cryptographic functions (Bash/Shell) | [skills/cryptography/T4454-test-cryptographic-functions-bash-shell/SKILL.md](skills/cryptography/T4454-test-cryptographic-functions-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T446 | Verify that only standard libraries are used for cryptography | [skills/cryptography/T446-verify-that-only-standard-libraries-are-used-for/SKILL.md](skills/cryptography/T446-verify-that-only-standard-libraries-are-used-for/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T59 | Use standard libraries for cryptography | [skills/cryptography/T59-python/SKILL.md](skills/cryptography/T59-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8547 |
| T60 | Use correct and approved cryptographic algorithms, parameters, and key lengths | [skills/cryptography/T60-python/SKILL.md](skills/cryptography/T60-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9492 |
| T87 | Verify that all data in transit is encrypted using a secure TLS channel | [skills/cryptography/T87-verify-that-all-data-in-transit-is-encrypted-usi/SKILL.md](skills/cryptography/T87-verify-that-all-data-in-transit-is-encrypted-usi/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T151 | Use cryptographically secure random numbers | [skills/cryptography/T151-python/SKILL.md](skills/cryptography/T151-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9352 |
| T156 | Validate certificate and its chain of trust properly | [skills/cryptography/T156-validate-certificate-and-its-chain-of-trust-prop/SKILL.md](skills/cryptography/T156-validate-certificate-and-its-chain-of-trust-prop/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T175 | Test that the client validates digital certificates | [skills/cryptography/T175-test-that-the-client-validates-digital-certifica/SKILL.md](skills/cryptography/T175-test-that-the-client-validates-digital-certifica/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2603 | Protect backup archive bits | [skills/cryptography/T2603-protect-backup-archive-bits/SKILL.md](skills/cryptography/T2603-protect-backup-archive-bits/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T2612 | Verify backup archive bits are protected | [skills/cryptography/T2612-verify-backup-archive-bits-are-protected/SKILL.md](skills/cryptography/T2612-verify-backup-archive-bits-are-protected/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T295 | Avoid storing unencrypted confidential data without access control mechanisms | [skills/cryptography/T295-python/SKILL.md](skills/cryptography/T295-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9517 |
| T296 | Test that unencrypted confidential data is not stored without access control mechanisms | [skills/cryptography/T296-test-that-unencrypted-confidential-data-is-not-s/SKILL.md](skills/cryptography/T296-test-that-unencrypted-confidential-data-is-not-s/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T587 | Verify that cryptographically secure algorithms are used for random number generation | [skills/cryptography/T587-verify-that-cryptographically-secure-algorithms/SKILL.md](skills/cryptography/T587-verify-that-cryptographically-secure-algorithms/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |

### database-security (11 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T2662 | Restrict network access to the database server | [skills/database-security/T2662-restrict-network-access-to-the-database-server/SKILL.md](skills/database-security/T2662-restrict-network-access-to-the-database-server/SKILL.md) | 10 | INFRA | Documented | TEMPLATE |
| T2605 | Validate database traffic | [skills/database-security/T2605-validate-database-traffic/SKILL.md](skills/database-security/T2605-validate-database-traffic/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2614 | Verify database traffic is validated | [skills/database-security/T2614-verify-database-traffic-is-validated/SKILL.md](skills/database-security/T2614-verify-database-traffic-is-validated/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2616 | Use a secure authentication mechanism for database connections (PostgreSQL) | [skills/database-security/T2616-use-a-secure-authentication-mechanism-for-databa/SKILL.md](skills/database-security/T2616-use-a-secure-authentication-mechanism-for-databa/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2652 | Consider adding plugins for stronger authentication protocols and stricter password complexity rules (MariaDB) | [skills/database-security/T2652-consider-adding-plugins-for-stronger-authenticat/SKILL.md](skills/database-security/T2652-consider-adding-plugins-for-stronger-authenticat/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2661 | Change insecure configuration defaults and remove unnecessary features | [skills/database-security/T2661-change-insecure-configuration-defaults-and-remov/SKILL.md](skills/database-security/T2661-change-insecure-configuration-defaults-and-remov/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2663 | Use a secure authentication mechanism for database connections | [skills/database-security/T2663-use-a-secure-authentication-mechanism-for-databa/SKILL.md](skills/database-security/T2663-use-a-secure-authentication-mechanism-for-databa/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |
| T2602 | Log typical database and server activities and related metadata | [skills/database-security/T2602-log-typical-database-and-server-activities-and-r/SKILL.md](skills/database-security/T2602-log-typical-database-and-server-activities-and-r/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2611 | Verify that typical database and server activities, along with related metadata, are logged | [skills/database-security/T2611-verify-that-typical-database-and-server-activiti/SKILL.md](skills/database-security/T2611-verify-that-typical-database-and-server-activiti/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2615 | Limit network access by blocking connections from unknown IP addresses (PostgreSQL) | [skills/database-security/T2615-limit-network-access-by-blocking-connections-fro/SKILL.md](skills/database-security/T2615-limit-network-access-by-blocking-connections-fro/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T2619 | Ensure that row-level security is correctly configured (PostgreSQL) | [skills/database-security/T2619-ensure-that-row-level-security-is-correctly-conf/SKILL.md](skills/database-security/T2619-ensure-that-row-level-security-is-correctly-conf/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |

### dependency-management (5 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T186 | Use recommended settings and the latest patches for third party libraries and software | [skills/dependency-management/T186-python/SKILL.md](skills/dependency-management/T186-python/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA9369 |
| T241 | Verify that third party libraries use secure settings and the latest patches | [skills/dependency-management/T241-verify-that-third-party-libraries-use-secure-set/SKILL.md](skills/dependency-management/T241-verify-that-third-party-libraries-use-secure-set/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7374 | Pin, hash, and continuously audit Python dependencies (FastAPI) | [skills/dependency-management/T7374-pin-hash-and-continuously-audit-python-dependenc/SKILL.md](skills/dependency-management/T7374-pin-hash-and-continuously-audit-python-dependenc/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T3913 | Implement package registry security (GitHub) | [skills/dependency-management/T3913-implement-package-registry-security-github/SKILL.md](skills/dependency-management/T3913-implement-package-registry-security-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T3930 | Test package registry security (GitHub) | [skills/dependency-management/T3930-test-package-registry-security-github/SKILL.md](skills/dependency-management/T3930-test-package-registry-security-github/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |

### infrastructure-hardening (13 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| CT9 | Ismenia | [skills/infrastructure-hardening/CT9-ismenia/SKILL.md](skills/infrastructure-hardening/CT9-ismenia/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T2349 | Configure software to have secure settings by default | [skills/infrastructure-hardening/T2349-configure-software-to-have-secure-settings-by-de/SKILL.md](skills/infrastructure-hardening/T2349-configure-software-to-have-secure-settings-by-de/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T2357 | Verify that software is configured to have secure settings by default | [skills/infrastructure-hardening/T2357-verify-that-software-is-configured-to-have-secur/SKILL.md](skills/infrastructure-hardening/T2357-verify-that-software-is-configured-to-have-secur/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T281 | Follow best practices when handling access tokens (API tokens) | [skills/infrastructure-hardening/T281-follow-best-practices-when-handling-access-token/SKILL.md](skills/infrastructure-hardening/T281-follow-best-practices-when-handling-access-token/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4441 | Prevent attacks related to environmental vulnerabilities (Bash/Shell) | [skills/infrastructure-hardening/T4441-prevent-attacks-related-to-environmental-vulnera/SKILL.md](skills/infrastructure-hardening/T4441-prevent-attacks-related-to-environmental-vulnera/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4442 | Manage and protect script processes (Bash/Shell) | [skills/infrastructure-hardening/T4442-manage-and-protect-script-processes-bash-shell/SKILL.md](skills/infrastructure-hardening/T4442-manage-and-protect-script-processes-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4452 | Test environmental vulnerabilities (Bash/Shell) | [skills/infrastructure-hardening/T4452-test-environmental-vulnerabilities-bash-shell/SKILL.md](skills/infrastructure-hardening/T4452-test-environmental-vulnerabilities-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4453 | Test protection of script processes (Bash/Shell) | [skills/infrastructure-hardening/T4453-test-protection-of-script-processes-bash-shell/SKILL.md](skills/infrastructure-hardening/T4453-test-protection-of-script-processes-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4601 | Prioritize static network configuration | [skills/infrastructure-hardening/T4601-prioritize-static-network-configuration/SKILL.md](skills/infrastructure-hardening/T4601-prioritize-static-network-configuration/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T105 | Verify that your application does not have unnecessary debug capability or leftover test/debug code | [skills/infrastructure-hardening/T105-verify-that-your-application-does-not-have-unnec/SKILL.md](skills/infrastructure-hardening/T105-verify-that-your-application-does-not-have-unnec/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T2258 | Minimize host OS attack surface | [skills/infrastructure-hardening/T2258-minimize-host-os-attack-surface/SKILL.md](skills/infrastructure-hardening/T2258-minimize-host-os-attack-surface/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T284 | Generate secure access tokens (API tokens) | [skills/infrastructure-hardening/T284-generate-secure-access-tokens-api-tokens/SKILL.md](skills/infrastructure-hardening/T284-generate-secure-access-tokens-api-tokens/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T49 | Disable and remove debug capabilities and code/data, and prepare application for release | [skills/infrastructure-hardening/T49-python/SKILL.md](skills/infrastructure-hardening/T49-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA8625 |

### input-validation (43 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T101 | Test that application is not vulnerable to SQL injection | [skills/input-validation/T101-test-that-application-is-not-vulnerable-to-sql-i/SKILL.md](skills/input-validation/T101-test-that-application-is-not-vulnerable-to-sql-i/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T122 | Test for remote file include | [skills/input-validation/T122-test-for-remote-file-include/SKILL.md](skills/input-validation/T122-test-for-remote-file-include/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T38 | Bind variables in SQL statements | [skills/input-validation/T38-python/SKILL.md](skills/input-validation/T38-python/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA9283 |
| T42 | Avoid relying on untrusted data for server-side selection | [skills/input-validation/T42-python/SKILL.md](skills/input-validation/T42-python/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA9489 |
| T43 | Avoid unsafe operating system interaction | [skills/input-validation/T43-python/SKILL.md](skills/input-validation/T43-python/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA9320 |
| T659 | Test that user-supplied inputs are validated before being passed to OS commands | [skills/input-validation/T659-test-that-user-supplied-inputs-are-validated-bef/SKILL.md](skills/input-validation/T659-test-that-user-supplied-inputs-are-validated-bef/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7359 | Prevent SQL injection with ORM queries and parameterized raw SQL (FastAPI) | [skills/input-validation/T7359-prevent-sql-injection-with-orm-queries-and-param/SKILL.md](skills/input-validation/T7359-prevent-sql-injection-with-orm-queries-and-param/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7360 | Block server-side request forgery in outbound and background-task calls (FastAPI) | [skills/input-validation/T7360-block-server-side-request-forgery-in-outbound-an/SKILL.md](skills/input-validation/T7360-block-server-side-request-forgery-in-outbound-an/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7366 | Validate and safely store uploaded files (FastAPI) | [skills/input-validation/T7366-validate-and-safely-store-uploaded-files-fastapi/SKILL.md](skills/input-validation/T7366-validate-and-safely-store-uploaded-files-fastapi/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7380 | Avoid OS command and dynamic code execution on user input (FastAPI) | [skills/input-validation/T7380-avoid-os-command-and-dynamic-code-execution-on-u/SKILL.md](skills/input-validation/T7380-avoid-os-command-and-dynamic-code-execution-on-u/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T7381 | Use safe parsers and never deserialize untrusted binary data (FastAPI) | [skills/input-validation/T7381-use-safe-parsers-and-never-deserialize-untrusted/SKILL.md](skills/input-validation/T7381-use-safe-parsers-and-never-deserialize-untrusted/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T2599 | Protect against connection string parameter pollution | [skills/input-validation/T2599-protect-against-connection-string-parameter-poll/SKILL.md](skills/input-validation/T2599-protect-against-connection-string-parameter-poll/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T2608 | Verify that the connection string is protected against connection string parameter pollution | [skills/input-validation/T2608-verify-that-the-connection-string-is-protected-a/SKILL.md](skills/input-validation/T2608-verify-that-the-connection-string-is-protected-a/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T7412 | Isolate dangerous functionality and risky third-party components using sandboxing or encapsulation | [skills/input-validation/T7412-isolate-dangerous-functionality-and-risky-third/SKILL.md](skills/input-validation/T7412-isolate-dangerous-functionality-and-risky-third/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T7415 | Verify that dangerous functionality and risky third-party components are isolated via sandboxing or encapsulation | [skills/input-validation/T7415-verify-that-dangerous-functionality-and-risky-th/SKILL.md](skills/input-validation/T7415-verify-that-dangerous-functionality-and-risky-th/SKILL.md) | 9 | CODE_FIX | Applied | TEMPLATE |
| T1144 | Prevent Server-Side Template Injection (SSTI) | [skills/input-validation/T1144-python/SKILL.md](skills/input-validation/T1144-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9360 |
| T1145 | Verify if web page template is vulnerable to SSTI | [skills/input-validation/T1145-verify-if-web-page-template-is-vulnerable-to-sst/SKILL.md](skills/input-validation/T1145-verify-if-web-page-template-is-vulnerable-to-sst/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T1365 | Mitigate Server Side Request Forgery | [skills/input-validation/T1365-python/SKILL.md](skills/input-validation/T1365-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8521 |
| T1392 | Test for Server Side Request Forgery | [skills/input-validation/T1392-test-for-server-side-request-forgery/SKILL.md](skills/input-validation/T1392-test-for-server-side-request-forgery/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T279 | Avoid dynamically loading any code without proper security considerations | [skills/input-validation/T279-avoid-dynamically-loading-any-code-without-prope/SKILL.md](skills/input-validation/T279-avoid-dynamically-loading-any-code-without-prope/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T305 | Verify that your application dynamically loads code only from secure locations | [skills/input-validation/T305-verify-that-your-application-dynamically-loads-c/SKILL.md](skills/input-validation/T305-verify-that-your-application-dynamically-loads-c/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T36 | Escape untrusted data in HTML, HTML attributes, CSS, and JavaScript | [skills/input-validation/T36-python/SKILL.md](skills/input-validation/T36-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA9293 |
| T4434 | Prevent injection attacks (Bash/Shell) | [skills/input-validation/T4434-python/SKILL.md](skills/input-validation/T4434-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8524 |
| T4435 | Prevent path traversal and file path manipulation (Bash/Shell) | [skills/input-validation/T4435-python/SKILL.md](skills/input-validation/T4435-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8554 |
| T4436 | Protect directory writing and reading (Bash/Shell) | [skills/input-validation/T4436-protect-directory-writing-and-reading-bash-shell/SKILL.md](skills/input-validation/T4436-protect-directory-writing-and-reading-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4437 | Prevent input file attacks (Bash/Shell) | [skills/input-validation/T4437-prevent-input-file-attacks-bash-shell/SKILL.md](skills/input-validation/T4437-prevent-input-file-attacks-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4438 | Prevent file upload vulnerabilities (Bash/Shell) | [skills/input-validation/T4438-python/SKILL.md](skills/input-validation/T4438-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8520 |
| T4445 | Test prevention of injection attacks (Bash/Shell) | [skills/input-validation/T4445-python/SKILL.md](skills/input-validation/T4445-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8591 |
| T4446 | Test prevention of path traversal and file path manipulation (Bash/Shell) | [skills/input-validation/T4446-python/SKILL.md](skills/input-validation/T4446-python/SKILL.md) | 8 | CODE_FIX | Applied | LIBRARY:TA8593 |
| T4447 | Test directory writing and reading (Bash/Shell) | [skills/input-validation/T4447-test-directory-writing-and-reading-bash-shell/SKILL.md](skills/input-validation/T4447-test-directory-writing-and-reading-bash-shell/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4448 | Test prevention against input file attacks (Bash/Shell) | [skills/input-validation/T4448-test-prevention-against-input-file-attacks-bash/SKILL.md](skills/input-validation/T4448-test-prevention-against-input-file-attacks-bash/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T4449 | Test prevention of file upload vulnerabilities (Bash/Shell) | [skills/input-validation/T4449-test-prevention-of-file-upload-vulnerabilities-b/SKILL.md](skills/input-validation/T4449-test-prevention-of-file-upload-vulnerabilities-b/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T573 | Prevent UDDI/ebXML spoofing | [skills/input-validation/T573-prevent-uddi-ebxml-spoofing/SKILL.md](skills/input-validation/T573-prevent-uddi-ebxml-spoofing/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T576 | Verify that UDDI/ebXML spoofing is prevented | [skills/input-validation/T576-verify-that-uddi-ebxml-spoofing-is-prevented/SKILL.md](skills/input-validation/T576-verify-that-uddi-ebxml-spoofing-is-prevented/SKILL.md) | 8 | INFRA | Documented | TEMPLATE |
| T7377 | Escape and sanitize user content in server-rendered HTML (FastAPI) | [skills/input-validation/T7377-escape-and-sanitize-user-content-in-server-rende/SKILL.md](skills/input-validation/T7377-escape-and-sanitize-user-content-in-server-rende/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T7378 | Restrict redirect targets to relative paths or an allowlist (FastAPI) | [skills/input-validation/T7378-restrict-redirect-targets-to-relative-paths-or-a/SKILL.md](skills/input-validation/T7378-restrict-redirect-targets-to-relative-paths-or-a/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T89 | Test that site is not vulnerable to XSS | [skills/input-validation/T89-test-that-site-is-not-vulnerable-to-xss/SKILL.md](skills/input-validation/T89-test-that-site-is-not-vulnerable-to-xss/SKILL.md) | 8 | CODE_FIX | Applied | TEMPLATE |
| T32 | Always perform input validation on a server | [skills/input-validation/T32-python/SKILL.md](skills/input-validation/T32-python/SKILL.md) | 7 | CODE_FIX | Applied | LIBRARY:TA9302 |
| T4433 | Prevent path environment attacks (Bash/Shell) | [skills/input-validation/T4433-prevent-path-environment-attacks-bash-shell/SKILL.md](skills/input-validation/T4433-prevent-path-environment-attacks-bash-shell/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T4444 | Test prevention of path environment attacks (Bash/Shell) | [skills/input-validation/T4444-test-prevention-of-path-environment-attacks-bash/SKILL.md](skills/input-validation/T4444-test-prevention-of-path-environment-attacks-bash/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T7411 | Implement controls for content intended to be displayed as text | [skills/input-validation/T7411-implement-controls-for-content-intended-to-be-di/SKILL.md](skills/input-validation/T7411-implement-controls-for-content-intended-to-be-di/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T7414 | Verify that content intended as text is rendered safely without XSS injection risk | [skills/input-validation/T7414-verify-that-content-intended-as-text-is-rendered/SKILL.md](skills/input-validation/T7414-verify-that-content-intended-as-text-is-rendered/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |
| T98 | Test for input validation on a server | [skills/input-validation/T98-test-for-input-validation-on-a-server/SKILL.md](skills/input-validation/T98-test-for-input-validation-on-a-server/SKILL.md) | 7 | CODE_FIX | Applied | TEMPLATE |

### logging-monitoring (3 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T7371 | Emit structured audit logs without leaking sensitive data (FastAPI) | [skills/logging-monitoring/T7371-emit-structured-audit-logs-without-leaking-sensi/SKILL.md](skills/logging-monitoring/T7371-emit-structured-audit-logs-without-leaking-sensi/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T349 | Protect audit information and logs against unauthorized access | [skills/logging-monitoring/T349-protect-audit-information-and-logs-against-unaut/SKILL.md](skills/logging-monitoring/T349-protect-audit-information-and-logs-against-unaut/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |
| T350 | Verify that audit information is sufficiently protected | [skills/logging-monitoring/T350-verify-that-audit-information-is-sufficiently-pr/SKILL.md](skills/logging-monitoring/T350-verify-that-audit-information-is-sufficiently-pr/SKILL.md) | 7 | INFRA | Documented | TEMPLATE |

### secrets-management (5 files)

| ID | Title | Skill File | Priority | Category | Status | Source |
|----|-------|------------|----------|----------|--------|--------|
| T1186 | Do not store secrets in Dockerfiles (Docker) | [skills/secrets-management/T1186-docker/SKILL.md](skills/secrets-management/T1186-docker/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA8441 |
| T1187 | Test if secrets are stored in Dockerfiles (Docker) | [skills/secrets-management/T1187-docker/SKILL.md](skills/secrets-management/T1187-docker/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA8466 |
| T7369 | Externalize the JWT signing key and other secrets from code (FastAPI) | [skills/secrets-management/T7369-externalize-the-jwt-signing-key-and-other-secret/SKILL.md](skills/secrets-management/T7369-externalize-the-jwt-signing-key-and-other-secret/SKILL.md) | 10 | CODE_FIX | Applied | TEMPLATE |
| T76 | Do not hardcode passwords | [skills/secrets-management/T76-python/SKILL.md](skills/secrets-management/T76-python/SKILL.md) | 10 | CODE_FIX | Applied | LIBRARY:TA8509 |
| T214 | Protect confidential files on operating system or server | [skills/secrets-management/T214-protect-confidential-files-on-operating-system-o/SKILL.md](skills/secrets-management/T214-protect-confidential-files-on-operating-system-o/SKILL.md) | 9 | INFRA | Documented | TEMPLATE |

## Completion Requirements

- Every one of the 276 skill files listed above must reach a terminal status.
- A CODE_FIX file is complete when its Required Fix is implemented and its Success Criteria hold.
- An INFRA file is complete when its guidance has been documented and routed to the owning team.
- Library-sourced files carry SD Elements' own content; apply them as written and do not edit the library text.
- Update the Status column in this table and the `**Status:**` line in each template file together.

## Progress Tracking

| Metric | Count |
|--------|-------|
| Total skill files | 276 |
| Pending | 255 |
| Applied | 21 |
| Documented | 0 |

## Verification Checklist

- [ ] All 276 skill files exist at the paths listed above
- [ ] All 276 file-tracked countermeasures are represented by at least one file
- [ ] The 71 library-sourced files match their SD Elements amendment byte for byte
- [ ] Every template file carries Category, SD Elements link, Priority and Status
- [ ] No countermeasure classified PROCESS has a skill file
- [ ] Status values in this index agree with the status inside each file

<!-- SDE-SECURITY-HARDENING-END -->
