#!/usr/bin/env python3
"""Build .sde-security/code-map.json.

The AI authors the CM -> (file, line-range, finding) mapping below after reading
and analyzing each file; this script only copies the current source lines
verbatim out of those files so the "Code to Fix" block in Step 9 is exact.
"""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(REPO, ".sde-security")

# cm_id: (path, start_line, end_line, finding)
MAP = {
    # ---- api-security ----
    "T116": ("app/init_app.py", 20, 26, "The CORS origin allow-list is a regular expression evaluated against the attacker-controlled Origin header; the unanchored `.*.` prefix makes matching input-dependent and the pattern is applied to every request."),
    "T119": ("app/init_app.py", 20, 29, "No middleware sets X-Frame-Options or a Content-Security-Policy frame-ancestors directive, so any page can frame the application's responses."),
    "T1363": ("app/rate_limiting.py", 1, 4, "A slowapi Limiter is constructed with no default limits, and no route in the application applies @limiter.limit, so no API throttling is actually enforced."),
    "T167": ("app/apis/orders/services/get_orders_service.py", 14, 29, "The endpoint returns a top-level JSON array of order records to a GET request, which is the classic shape exploited by JSON hijacking when the response is reachable with ambient credentials."),
    "T2140": ("app/apis/debug/services/get_debug_info_service.py", 22, 27, "The debug response embeds the full process environment plus the working directory, sys.path and a directory listing, exposing internal configuration and secrets through an API."),
    "T228": ("app/init_app.py", 11, 19, "The FastAPI application is constructed with no request-body size limit middleware, so an arbitrarily large body is buffered before any handler runs."),
    "T2596": ("docker-compose.yml", 2, 8, "Uvicorn is published directly on port 8091 with no hardened reverse proxy in front, so conflicting Content-Length/Transfer-Encoding handling between hops is never normalized."),
    "T2600": ("app/apis/orders/services/get_orders_for_delivery_service.py", 17, 32, "`limit` is an unconstrained integer query parameter passed straight into .limit(), so a caller can request an unbounded result set."),
    "T318": ("app/init_app.py", 20, 26, "CORS is configured with a permissive unanchored origin regex together with allow_credentials=True and wildcard methods and headers."),
    "T35": ("docker-compose.yml", 2, 8, "The server is started with --reload and a single worker and no request/keep-alive timeouts or concurrency limits configured."),
    "T536": ("app/init_app.py", 11, 19, "No maximum request size is enforced at the application or middleware layer."),
    "T537": ("app/init_app.py", 11, 19, "There is no body-size ceiling to test against: the application accepts requests of any length."),
    "T66": ("app/init_app.py", 20, 29, "No framing protection header is emitted by the middleware stack."),
    "T7357": ("app/apis/auth/services/patch_profile_service.py", 22, 25, "The profile update model is declared with extra=Extra.allow, so unknown client-supplied fields survive validation and are later assigned onto the ORM object."),
    "T7358": ("app/apis/debug/services/get_debug_info_service.py", 11, 12, "The route declares no response_model, so whatever the handler builds — including the environment dump — is serialized to the client unfiltered."),
    "T7361": ("app/init_app.py", 20, 26, "allow_credentials=True is combined with a wildcard-ish origin regex and wildcard methods and headers."),
    "T7362": ("app/init_app.py", 11, 19, "Neither TrustedHostMiddleware nor HTTPSRedirectMiddleware is installed, so Host headers are unvalidated and plaintext HTTP is served."),
    "T7363": ("app/init_app.py", 20, 29, "The middleware stack adds CORS and a rate-limit handler but no security response headers."),
    "T7364": ("app/apis/menu/utils.py", 9, 13, "The remote image is downloaded and base64-encoded entirely in memory with no Content-Length check and no size cap."),
    "T7365": ("app/apis/auth/services/get_token_service.py", 16, 21, "The token endpoint carries no rate-limit decorator, so password guessing is unthrottled."),
    "T7368": ("app/apis/auth/services/get_token_service.py", 26, 32, "The access token is returned in the response body with no cookie attributes and no CSRF token issued alongside it."),
    "T7370": ("app/apis/admin/utils.py", 11, 13, "A bare except swallows the real error and re-raises a generic Exception, which FastAPI surfaces as an unhandled 500 with a traceback when debug output is enabled."),
    "T7372": ("app/main.py", 23, 29, "Swagger UI is re-registered at /docs unconditionally, with no environment guard, after being disabled in the FastAPI constructor."),
    "T7373": ("app/apis/admin/services/reset_chef_password_service.py", 22, 28, "Authorization is decided from request.client.host alone, with no proxy allow-list and no validation of forwarded headers."),
    "T7375": ("app/apis/auth/services/register_user_service.py", 19, 40, "The handler is declared `async def` but calls create_user, which performs a blocking bcrypt hash and synchronous database work directly on the event loop."),
    "T7376": ("pyproject.toml", 42, 48, "The pytest configuration defines no security regression suite or marker; the existing tests cover functional behavior only."),
    "T7379": ("app/main.py", 11, 13, "StaticFiles is mounted on a relative \"static\" directory resolved from the process working directory rather than an explicit, dedicated path."),
    "T7382": ("app/apis/referrals/service.py", 47, 74, "Applying a referral code creates a new discount coupon every time it is called, with no idempotency key or one-per-user guard, so the request can be replayed for unlimited coupons."),
    "T96": ("app/apis/auth/services/patch_profile_service.py", 28, 33, "A state-changing PATCH is accepted with no CSRF token and no origin check."),

    # ---- authentication ----
    "T114": ("app/apis/auth/services/get_token_service.py", 16, 27, "Failed authentications are returned immediately with no counter, lockout or backoff for machine accounts."),
    "T1539": ("app/apis/auth/service.py", 12, 19, "The auth router registers no logout route, so there is nothing that invalidates the token or instructs the client to clear stored credentials."),
    "T1540": ("app/apis/auth/service.py", 12, 19, "With no logout endpoint there is no server-side signal to verify that client-side data is cleared."),
    "T2276": ("app/apis/orders/services/get_orders_for_delivery_service.py", 12, 21, "The delivery orders endpoint declares no authentication or authorization dependency and is merely hidden from the schema."),
    "T230": ("app/init.py", 30, 38, "A seeded employee account uses the password \"kaylee123\", which meets no strength requirement."),
    "T323": ("app/init.py", 30, 73, "Five accounts are seeded with hardcoded, weak passwords that are never forced to change."),
    "T395": ("app/apis/auth/utils/text_code_utils.py", 10, 17, "The one-time reset code is only four decimal digits and its delivery is not tied to any attempt counter."),
    "T406": ("app/apis/auth/utils/utils.py", 10, 11, "The symmetric HS256 signing key is taken from Settings.JWT_SECRET_KEY, which falls back to a six-digit random value."),
    "T407": ("app/apis/auth/utils/jwt_auth.py", 11, 13, "The verifier loads the same weak symmetric key and then disables signature verification outright."),
    "T4439": ("start_app.sh", 1, 4, "The startup script invokes docker compose with no authentication or identity check on the caller."),
    "T4450": ("start_app.sh", 1, 4, "There is no authentication step in the operational scripts to exercise."),
    "T558": ("app/apis/menu/utils.py", 9, 11, "The outbound HTTP call to an arbitrary image host presents no client credentials and performs no mutual authentication."),
    "T589": ("app/apis/orders/utils.py", 4, 15, "The delivery-service integration point returns data without authenticating the remote component."),
    "T61": ("app/init.py", 30, 73, "Default accounts for Mike, Saul, hhm, johndoe and alicesmith are created with fixed passwords and left enabled."),
    "T7353": ("app/apis/auth/utils/jwt_auth.py", 28, 33, "jwt.decode is called with options={\"verify_signature\": False}, so any unsigned or forged token is accepted."),
    "T7354": ("app/apis/auth/utils/utils.py", 13, 21, "The password context pins bcrypt with deprecated=\"auto\" and no explicit cost factor, and Argon2 is not offered."),
    "T7367": ("app/apis/router.py", 12, 22, "No WebSocket route is registered and no handshake origin/authentication policy exists for future ones."),
    "T78": ("app/apis/auth/services/reset_password_new_password_service.py", 36, 46, "The reset code is compared with no attempt limit and no rate limiting, so the four-digit code is brute-forceable within its fifteen-minute window."),
    "T86": ("app/apis/auth/services/get_token_service.py", 28, 32, "A new access token is minted with no session identifier, no jti and no invalidation of tokens issued before authentication."),

    # ---- authorization ----
    "T106": ("app/apis/orders/services/get_order_service.py", 11, 20, "The order is fetched by path id and returned without comparing Order.user_id to the caller."),
    "T128": ("app/apis/users/services/update_user_role_service.py", 13, 25, "The target account is selected by a client-supplied username and updated with no check that the caller may modify it."),
    "T15": ("app/apis/auth/utils/roles_based_auth_checker.py", 6, 17, "RolesBasedAuthChecker is the only shared authorization primitive and it covers roles alone; ownership and resource rules are re-implemented ad hoc in individual handlers."),
    "T226": ("app/apis/admin/services/get_disk_stats_service.py", 21, 24, "The role check is written inline in the handler instead of going through the shared authorization dependency."),
    "T2282": ("app/apis/debug/services/get_debug_info_service.py", 11, 12, "The /debug route is registered with no authentication dependency and is reachable anonymously."),
    "T373": ("app/apis/router.py", 12, 22, "Routers are mounted without an explicit policy separating the authenticated surface from the anonymous one; /debug and /delivery/orders end up public by omission."),
    "T378": ("app/apis/orders/services/get_order_service.py", 11, 20, "A role check is present but no per-object authorization is performed on the requested order."),
    "T4440": ("stop_app.sh", 1, 3, "The teardown script performs a privileged compose action with no access control on who may run it."),
    "T4451": ("stop_app.sh", 1, 3, "There is no access-control logic in the script to exercise."),
    "T7355": ("app/apis/menu/services/delete_menu_item_service.py", 12, 18, "Unlike create and update, the delete route depends only on get_current_user and applies no RolesBasedAuthChecker, so any authenticated customer can delete menu items."),
    "T7356": ("app/apis/orders/services/get_order_service.py", 11, 20, "No ownership predicate is applied to the queried Order before it is serialized back."),
    "T85": ("app/apis/users/services/update_user_role_service.py", 13, 25, "The only server-side check rejects the Chef role; every other role change is applied to any username without verifying the caller's privileges."),

    # ---- ci-cd-security ----
    "T3915": ("docker-compose.yml", 15, 20, "Deployment configuration and credentials are inlined in the committed compose file rather than separated per environment."),
    "T3932": ("docker-compose.yml", 15, 20, "There is a single committed compose file holding environment values, so separation cannot be verified."),

    # ---- container-security ----
    "T1175": ("Dockerfile", 20, 25, "A non-root user is created only after a sudoers rule granting passwordless sudo is installed, so the container user can regain root."),
    "T1193": ("docker-compose.yml", 5, 6, "The host source tree is bind-mounted read-write into the container at /app."),
    "T1195": ("Dockerfile", 12, 14, "The runtime image installs interactive tooling (vim, sudo, gcc) that expands the in-container administrative surface."),
    "T1197": ("docker-compose.yml", 7, 8, "Port 8091 is published to all host interfaces with no bind address restriction."),
    "T1199": ("docker-compose.yml", 2, 8, "The service definition relies on default networking with no explicit network mode declared or pinned."),
    "T1201": ("docker-compose.yml", 2, 14, "No memory, pids or ulimit constraints are declared for the web service."),
    "T1203": ("docker-compose.yml", 2, 14, "Neither cpu_shares nor cpus is set, so the container competes for host CPU without bound."),
    "T1205": ("docker-compose.yml", 2, 14, "read_only is not set, so the container root filesystem is writable."),
    "T1207": ("docker-compose.yml", 2, 14, "No restart policy is declared for the web service."),
    "T1209": ("docker-compose.yml", 5, 6, "The bind mount is declared in short-string form, so propagation mode is neither stated nor constrained."),
    "T1211": ("docker-compose.yml", 12, 14, "privileged: true disables the default seccomp profile for the container."),
    "T1213": ("docker-compose.yml", 12, 14, "Running privileged with SYS_ADMIN gives the container control over cgroup configuration."),
    "T1215": ("docker-compose.yml", 12, 14, "no-new-privileges is not set in security_opt, and privileged mode would override it."),
    "T1917": ("Dockerfile", 10, 20, "The runtime stage installs a compiler and sudo and grants a passwordless sudoers rule, none of which is covered by any image assessment step."),
    "T4746": ("Dockerfile", 1, 10, "Both stages reference floating tags (python:3.10-bookworm, python:3.10-slim-bookworm) with no digest pinning or provenance verification."),
    "T4747": ("docker-compose.yml", 12, 14, "The web container runs privileged and additionally requests the SYS_ADMIN capability."),
    "T4750": ("docker-compose.yml", 1, 20, "No user-defined network is declared, so web and db share the default bridge with no segmentation."),
    "T4751": ("Dockerfile", 12, 14, "apt-get installs gcc, vim and sudo into the runtime image and never cleans the apt lists."),

    # ---- cryptography ----
    "T1468": ("app/apis/auth/services/get_token_service.py", 29, 32, "The bearer token is handed to the client with no guidance or mechanism for protecting it at rest on the client side."),
    "T156": ("app/apis/menu/utils.py", 9, 11, "requests.get is called on a caller-supplied URL with no explicit certificate verification or CA bundle configuration."),
    "T175": ("app/apis/menu/utils.py", 9, 11, "The outbound client's certificate validation behavior is left entirely to defaults and is never asserted."),
    "T197": ("app/apis/menu/utils.py", 9, 13, "Remote content is fetched and stored with no signature or integrity check on its origin."),
    "T2485": ("pyproject.toml", 9, 31, "Dependencies are declared with caret ranges and no hashes, so the integrity of fetched packages is never verified."),
    "T2486": ("pyproject.toml", 9, 31, "There is no signing or integrity metadata for the code the service pulls in at build time."),
    "T296": ("app/db/models.py", 33, 45, "reset_password_code and phone_number are stored as plain columns with no encryption and no column-level access control."),
    "T439": ("app/apis/menu/utils.py", 9, 13, "Content retrieved from a remote origin is accepted without any integrity verification before it is persisted and later served."),
    "T4443": ("start_app.sh", 1, 4, "The operational scripts handle no key material and provide no cryptographic controls around the secrets passed into the containers."),
    "T4454": ("start_app.sh", 1, 4, "There are no cryptographic functions in the shell tooling to exercise."),
    "T445": ("app/apis/auth/utils/utils.py", 10, 11, "HS256 is used with a key that defaults to six decimal digits, far below any approved key-length requirement."),
    "T446": ("app/apis/referrals/utils.py", 1, 11, "Referral codes are generated with the standard `random` module rather than a cryptographic library."),
    "T587": ("app/apis/referrals/utils.py", 8, 11, "random.choice draws from a predictable Mersenne Twister stream, so referral codes are guessable."),
    "T87": ("app/db/session.py", 21, 22, "The PostgreSQL engine is created from a URL with no sslmode, so the database connection can run in plaintext."),

    # ---- dependency-management ----
    "T241": ("pyproject.toml", 9, 31, "Every dependency is declared with a caret range and no lower-bound security floor or audit step."),
    "T7374": ("pyproject.toml", 9, 31, "Dependencies are unpinned caret ranges with no hash verification and no scheduled audit."),

    # ---- infrastructure-hardening ----
    "CT9": ("app/config.py", 13, 19, "The environment selector defaults to PRODUCTION while every other default in this module is a development convenience, so the deployed configuration is not deliberately chosen."),
    "T105": ("app/apis/debug/services/get_debug_info_service.py", 11, 12, "A debug information endpoint ships in the application and is only hidden from the OpenAPI schema."),
    "T2349": ("app/config.py", 26, 36, "Every security-relevant setting falls back to an insecure development default: a six-digit JWT key, the username \"chef\" and the database password \"password\"."),
    "T2357": ("app/config.py", 26, 36, "The insecure fallbacks apply silently whenever the environment variables are absent, so there is no secure-by-default baseline to verify."),
    "T281": ("app/apis/auth/utils/utils.py", 117, 125, "Access tokens are minted with only an exp claim — no issuer, audience, jti or revocation support — and the caller chooses the lifetime."),
    "T284": ("app/config.py", 22, 27, "The fallback signing secret is six decimal digits drawn from the non-cryptographic `random` module."),
    "T4441": ("start_app.sh", 1, 4, "The script runs with the caller's inherited environment and PATH and passes it straight into the container runtime."),
    "T4442": ("stop_app.sh", 1, 3, "The teardown script starts a privileged process with no process isolation, locking or signal handling."),
    "T4452": ("start_game.sh", 1, 4, "The script invokes a sibling script by relative path, resolving it from the caller's working directory and environment."),
    "T4453": ("start_game.sh", 1, 4, "A second process is launched inside the running container with no supervision, timeout or cleanup."),

    # ---- input-validation ----
    "T101": ("app/apis/orders/services/get_order_status.py", 36, 42, "The UPDATE statement is built by f-string interpolation of status_value and order_id and executed through text(), so it is directly injectable."),
    "T1145": ("app/main.py", 15, 21, "Documentation HTML is generated by interpolating app.root_path into URLs handed to the Swagger UI template helper."),
    "T122": ("app/apis/menu/utils.py", 9, 13, "A caller-supplied URL is fetched and its bytes are embedded in the application's own responses."),
    "T1392": ("app/apis/menu/utils.py", 9, 13, "requests.get is issued against an unvalidated caller-supplied URL, reaching internal addresses and non-HTTP schemes."),
    "T2599": ("app/config.py", 49, 53, "The database URL is assembled by string interpolation of five environment values with no escaping, so a value containing a delimiter can inject connection parameters."),
    "T2608": ("app/config.py", 49, 53, "There is no encoding or validation of the interpolated credentials and host components to verify against."),
    "T279": ("app/apis/menu/utils.py", 9, 13, "Arbitrary remote bytes are pulled in at request time and stored for later use with no source restriction."),
    "T305": ("app/main.py", 11, 13, "The static mount resolves \"static\" relative to the process working directory rather than an absolute, trusted location."),
    "T4433": ("start_app.sh", 1, 4, "Commands are invoked by bare name, so resolution depends on the inherited PATH."),
    "T4436": ("start_app.sh", 1, 4, "mkdir -p creates postgres_data relative to the caller's working directory with default permissions."),
    "T4437": ("start_game.sh", 1, 4, "The script executes a relative-path script and a file inside the container without validating either."),
    "T4444": ("start_app.sh", 1, 4, "There is no PATH hardening in the script to exercise."),
    "T4447": ("start_app.sh", 1, 4, "Directory creation applies no explicit mode and no ownership check."),
    "T4448": ("start_game.sh", 1, 4, "Input files consumed by the script are not validated before execution."),
    "T4449": ("start_game.sh", 1, 4, "The script copies no uploaded content but also applies no validation to the files it hands to the container."),
    "T659": ("app/apis/admin/utils.py", 4, 10, "The `parameters` string is concatenated onto \"df -h \" and executed with shell=True, giving direct command injection."),
    "T7359": ("app/apis/orders/services/get_order_status.py", 36, 42, "Raw SQL is assembled with f-string interpolation instead of bound parameters or the ORM."),
    "T7360": ("app/apis/menu/utils.py", 9, 13, "The outbound request target comes straight from the request body with no scheme, host or address validation."),
    "T7366": ("app/apis/menu/utils.py", 16, 31, "Remote image bytes are base64-encoded and stored with no content-type check, no magic-byte validation and no size limit."),
    "T7377": ("app/main.py", 15, 21, "Server-rendered documentation HTML interpolates configuration values without escaping."),
    "T7378": ("app/apis/menu/utils.py", 9, 11, "requests.get follows redirects by default from a caller-supplied URL, so the final target is attacker-chosen."),
    "T7380": ("app/apis/admin/utils.py", 4, 10, "A shell is spawned with a command string built from request input."),
    "T7381": ("app/apis/menu/utils.py", 9, 13, "Untrusted remote binary content is ingested and re-encoded with no parser restrictions."),
    "T7411": ("app/apis/menu/services/create_menu_item_service.py", 15, 22, "Menu item name and description are accepted as free text and persisted with no output-encoding contract."),
    "T7412": ("app/apis/admin/utils.py", 4, 10, "The subprocess call runs in the application's own process context with no sandbox or privilege separation."),
    "T7414": ("app/apis/menu/services/create_menu_item_service.py", 15, 22, "Stored text fields are returned verbatim through the API with no encoding guarantee for HTML consumers."),
    "T7415": ("docker-compose.yml", 12, 14, "The container that executes shell commands on request runs privileged with SYS_ADMIN, so nothing is isolated."),
    "T89": ("app/apis/menu/utils.py", 34, 55, "Update writes caller-supplied text fields straight onto the model and back out through the API with no sanitization."),
    "T98": ("app/apis/admin/services/get_disk_stats_service.py", 16, 27, "The `parameters` query string is accepted with no validation and handed to a shell command builder."),

    # ---- logging-monitoring ----
    "T7371": ("app/init_app.py", 10, 32, "The application factory configures no logging at all, so no structured audit record is produced for authentication, authorization or administrative actions."),

    # ---- secrets-management ----
    "T7369": ("app/config.py", 22, 27, "JWT_SECRET_KEY falls back to an in-process generated six-digit value instead of requiring an externally supplied secret."),
}


def main():
    cls = json.load(open(os.path.join(SEC, "classification.json"), encoding="utf-8"))
    todo = json.load(open(os.path.join(SEC, "code-map-todo.json"), encoding="utf-8"))
    missing = [c for c in todo if c not in MAP]
    extra = [c for c in MAP if c not in todo]
    if missing or extra:
        print("MISSING:", missing)
        print("EXTRA:", extra)
        sys.exit(1)

    out = {}
    for cm, (path, start, end, finding) in MAP.items():
        full = os.path.join(REPO, path)
        lines = open(full, encoding="utf-8").read().split("\n")
        assert 1 <= start <= end <= len(lines), f"{cm}: bad range for {path}"
        snippet = "\n".join(lines[start - 1:end]).rstrip()
        out[cm] = {
            "cm_id": cm,
            "domain": cls[cm]["domain"],
            "file": path,
            "start_line": start,
            "end_line": end,
            "language": {"py": "python", "yml": "yaml", "sh": "bash", "toml": "toml"}[path.rsplit(".", 1)[-1]] if "." in os.path.basename(path) else "dockerfile",
            "finding": finding,
            "snippet": snippet,
        }
    json.dump(out, open(os.path.join(SEC, "code-map.json"), "w", encoding="utf-8"), indent=2)
    print(f"code-map.json written: {len(out)} CMs")
    files = {}
    for v in out.values():
        files[v["file"]] = files.get(v["file"], 0) + 1
    for f, n in sorted(files.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {f}")


if __name__ == "__main__":
    main()
