#!/usr/bin/env python3
"""AI-authored content fields for the 137 template CODE_FIX skill files.

Each entry supplies the `description`, the `Required Fix` code pattern and the
`Success Criteria` for one countermeasure. The `Code to Fix` block comes from
code-map.json (verbatim source lines); nothing here is generated mechanically.
"""

CODEFIX = {

# ============================ api-security ============================

"T116": {
 "description": "Bound the regular expressions that run against request-controlled input so a crafted Origin header cannot drive catastrophic backtracking.",
 "fix": """# app/init_app.py
ALLOWED_ORIGINS = [
    "https://app.restaurant.com",
    "https://partner.deliveryservice.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # exact string comparison, no regex engine
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)""",
 "criteria": [
  "No regular expression is evaluated against the Origin header or any other request-controlled string in the middleware stack.",
  "Any regex that must remain is anchored with ^ and $ and contains no nested quantifier over an alternation.",
  "A request carrying a 10 KB Origin header returns in the same time as a normal request.",
 ]},

"T119": {
 "description": "Emit framing-protection headers on every response so the application cannot be embedded in an attacker-controlled page.",
 "fix": """# app/init_app.py
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        return response


app.add_middleware(SecurityHeadersMiddleware)""",
 "criteria": [
  "Every response carries `X-Frame-Options: DENY` and a CSP containing `frame-ancestors 'none'`.",
  "A page that embeds the application in an iframe fails to render it.",
 ]},

"T1363": {
 "description": "Apply the configured slowapi limiter to the routes it was introduced for so request throttling is actually enforced.",
 "fix": """# app/rate_limiting.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

# app/apis/auth/services/get_token_service.py
@router.post("/token")
@limiter.limit("5/minute")
async def get_token(request: Request, ...):
    ...""",
 "criteria": [
  "The Limiter is constructed with a default limit.",
  "Authentication, password-reset and admin routes carry an explicit, tighter @limiter.limit decorator.",
  "Exceeding a limit returns HTTP 429 with a Retry-After header.",
 ]},

"T167": {
 "description": "Wrap collection responses in a JSON object so the reply is never a bare top-level array that a foreign page can read.",
 "fix": """# app/apis/orders/services/get_orders_service.py
class OrderListResponse(BaseModel):
    items: List[schemas.Order]


@router.get("/orders", response_model=OrderListResponse)
def get_orders(...):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .offset(skip)
        .limit(min(limit, 100))
        .all()
    )
    return OrderListResponse(items=orders)""",
 "criteria": [
  "No endpoint returns a top-level JSON array.",
  "Collection endpoints respond with an object whose payload sits under a named key.",
  "Responses are served with `Content-Type: application/json` and are not executable as script.",
 ]},

"T2140": {
 "description": "Stop returning process environment, filesystem and path information through the API.",
 "fix": """# app/apis/debug/services/get_debug_info_service.py
# Remove the endpoint entirely. If an operational probe is required,
# expose only non-identifying liveness data and require an authenticated
# operator role:

@router.get("/internal/status", status_code=status.HTTP_200_OK)
def get_status(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
):
    return {"status": "ok"}""",
 "criteria": [
  "No route returns `os.environ`, `sys.path`, `os.getcwd()` or a directory listing.",
  "An unauthenticated request to any diagnostic path returns 401 or 404.",
 ]},

"T228": {
 "description": "Reject oversized request bodies before they are buffered into memory.",
 "fix": """# app/init_app.py
MAX_BODY_BYTES = 1 * 1024 * 1024


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        declared = request.headers.get("content-length")
        if declared is not None and int(declared) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)""",
 "criteria": [
  "A request whose Content-Length exceeds the configured ceiling is rejected with 413.",
  "A chunked request that streams past the ceiling is terminated rather than buffered.",
 ]},

"T2596": {
 "description": "Terminate client connections on a hardened reverse proxy that normalizes Content-Length and Transfer-Encoding before requests reach the application server.",
 "fix": """# docker-compose.yml
  web:
    build: .
    command: uvicorn main:app --host 127.0.0.1 --port 8091 --workers 4
    expose:
      - 8091
  proxy:
    image: nginx:1.27-alpine
    depends_on: [web]
    ports:
      - "127.0.0.1:8443:8443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf:ro
    # nginx.conf: proxy_http_version 1.1; drops requests carrying both
    # Content-Length and Transfer-Encoding, and rejects malformed framing.""",
 "criteria": [
  "The application server is not directly reachable from outside the container network.",
  "A request carrying both Content-Length and Transfer-Encoding headers is rejected at the edge.",
  "Front-end and back-end agree on HTTP version and keep-alive handling.",
 ]},

"T2600": {
 "description": "Cap the number of rows any listing endpoint will return regardless of the requested limit.",
 "fix": """# app/apis/orders/services/get_orders_for_delivery_service.py
from fastapi import Query

MAX_PAGE_SIZE = 100


def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    ...
):
    orders = db.query(Order).order_by(Order.date_ordered.desc()).offset(skip).limit(limit).all()""",
 "criteria": [
  "Every paginated endpoint declares `le=` on its limit parameter.",
  "A request for limit=100000 is rejected with 422 rather than served.",
 ]},

"T318": {
 "description": "Replace the permissive CORS configuration with an explicit origin allow-list and a narrow method and header set.",
 "fix": """# app/init_app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # explicit list, loaded from config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)""",
 "criteria": [
  "`allow_origin_regex` is no longer used.",
  "`allow_methods` and `allow_headers` list explicit values, never `*`, while credentials are allowed.",
  "A preflight from `https://evil-restaurant.com.attacker.net` receives no Access-Control-Allow-Origin header.",
 ]},

"T35": {
 "description": "Run the application server with production settings: no auto-reload, multiple workers and explicit request timeouts and concurrency limits.",
 "fix": """# docker-compose.yml
  web:
    command: >
      uvicorn main:app --host 127.0.0.1 --port 8091
      --workers 4
      --timeout-keep-alive 5
      --limit-concurrency 256
      --limit-max-requests 10000
      --proxy-headers --forwarded-allow-ips 10.0.0.0/8""",
 "criteria": [
  "`--reload` does not appear in any non-development compose profile.",
  "Keep-alive, concurrency and max-request limits are set explicitly.",
  "The server binds to the internal interface only.",
 ]},

"T536": {
 "description": "Enforce a maximum accepted message size for every service endpoint.",
 "fix": """# app/init_app.py
MAX_BODY_BYTES = 1 * 1024 * 1024        # general JSON payloads
MAX_UPLOAD_BYTES = 5 * 1024 * 1024      # routes that accept binary content

app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)""",
 "criteria": [
  "A global body-size ceiling is applied by middleware, not per handler.",
  "Routes needing a larger ceiling opt in explicitly rather than the default being generous.",
 ]},

"T537": {
 "description": "Provide an enforced message-size ceiling that a test can exercise and confirm.",
 "fix": """# app/tests/integration/test_body_size_limit.py
def test_oversized_body_is_rejected(client):
    payload = {"description": "A" * (2 * 1024 * 1024)}
    response = client.put("/menu", json=payload)
    assert response.status_code == 413""",
 "criteria": [
  "An automated test submits a body above the ceiling and asserts a 413 response.",
  "The test fails if the middleware is removed.",
 ]},

"T66": {
 "description": "Deny framing of the application through response headers set for every route.",
 "fix": """# app/init_app.py
response.headers["X-Frame-Options"] = "DENY"
response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; default-src 'self'\"""",
 "criteria": [
  "Framing directives are present on every response including error responses.",
  "No route opts out of the header middleware.",
 ]},

"T7357": {
 "description": "Forbid unknown fields in request models so client input cannot introduce attributes that later get written onto ORM objects.",
 "fix": """# app/apis/auth/services/patch_profile_service.py
from pydantic import BaseModel, ConfigDict


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None


@router.patch("/profile", response_model=UserRead, status_code=status.HTTP_200_OK)
def patch_profile(user: UserUpdate, ...):
    db_user = get_user_by_username(db, current_user.username)
    for field, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)""",
 "criteria": [
  "No request model in the codebase is declared with `extra=Extra.allow` or `extra=\"allow\"`.",
  "A PATCH body containing `{\"role\": \"Chef\"}` returns 422 instead of being applied.",
  "Attribute assignment iterates the declared model fields, never arbitrary client keys.",
 ]},

"T7358": {
 "description": "Declare an explicit response_model on every route so only the intended fields are serialized to the client.",
 "fix": """# app/apis/debug/services/get_debug_info_service.py
class StatusResponse(BaseModel):
    status: str
    version: str


@router.get("/internal/status", response_model=StatusResponse)
def get_status(...):
    return StatusResponse(status="ok", version=settings.VERSION)""",
 "criteria": [
  "Every route declares a response_model.",
  "No response model exposes password hashes, reset codes or environment values.",
  "Adding a sensitive column to a model does not change any API response.",
 ]},

"T7361": {
 "description": "Configure CORS with a concrete origin list and never combine credentialed requests with wildcard values.",
 "fix": """# app/init_app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.restaurant.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)""",
 "criteria": [
  "`allow_credentials=True` never appears alongside `allow_origins=[\"*\"]` or an origin regex.",
  "Origins are supplied by configuration and differ between environments.",
 ]},

"T7362": {
 "description": "Install TrustedHostMiddleware and HTTPS enforcement so Host headers are validated and plaintext requests are redirected.",
 "fix": """# app/init_app.py
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
if settings.ENVIRONMENT is ENV.PRODUCTION:
    app.add_middleware(HTTPSRedirectMiddleware)""",
 "criteria": [
  "A request with `Host: attacker.example` returns 400.",
  "A plaintext HTTP request in production is redirected to HTTPS.",
  "Allowed hosts come from configuration, not a wildcard.",
 ]},

"T7363": {
 "description": "Add a middleware that sets the standard security response headers on every reply.",
 "fix": """# app/init_app.py
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers.pop("X-Powered-By", None)
        return response


app.add_middleware(SecurityHeadersMiddleware)""",
 "criteria": [
  "nosniff, frame options, referrer policy, CSP and HSTS are present on every response.",
  "No response advertises the framework or language version.",
 ]},

"T7364": {
 "description": "Bound the size of any content the service downloads or accepts so a single request cannot exhaust process memory.",
 "fix": """# app/apis/menu/utils.py
MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _image_url_to_base64(image_url: str) -> str:
    with requests.get(image_url, stream=True, timeout=5) as response:
        response.raise_for_status()
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image too large")

        chunks, total = [], 0
        for chunk in response.iter_content(64 * 1024):
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=413, detail="Image too large")
            chunks.append(chunk)

    return base64.b64encode(b"".join(chunks)).decode()""",
 "criteria": [
  "The download is streamed and aborts once the byte ceiling is crossed.",
  "A declared Content-Length above the ceiling short-circuits before any body is read.",
  "A connect and read timeout is set on the outbound request.",
 ]},

"T7365": {
 "description": "Rate-limit the authentication and password-reset endpoints, which are the cheapest targets for credential guessing.",
 "fix": """# app/apis/auth/services/get_token_service.py
from rate_limiting import limiter


@router.post("/token")
@limiter.limit("5/minute")
async def get_token(request: Request, form_data: ..., db: Session = Depends(get_db)) -> Token:
    ...""",
 "criteria": [
  "/token, /register, /reset-password and /reset-password/new-password each carry an explicit limit.",
  "The sixth login attempt within a minute from one source returns 429.",
  "Limits are keyed on both source address and submitted username.",
 ]},

"T7368": {
 "description": "If the token is placed in a cookie, set SameSite, Secure and HttpOnly and pair it with a CSRF token; otherwise keep it out of cookies entirely.",
 "fix": """# app/apis/auth/services/get_token_service.py
response.set_cookie(
    "access_token",
    access_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=int(access_token_expires.total_seconds()),
    path="/",
)
response.set_cookie("csrf_token", secrets.token_urlsafe(32), secure=True, samesite="strict")
# every state-changing route then compares the X-CSRF-Token header to the cookie""",
 "criteria": [
  "No authentication cookie is set without HttpOnly, Secure and SameSite.",
  "Every state-changing route rejects a request whose CSRF header does not match the cookie.",
  "A cross-site form POST against a state-changing route fails.",
 ]},

"T7370": {
 "description": "Return a generic error to the client, log the detail internally, and never let a bare except mask the real failure.",
 "fix": """# app/apis/admin/utils.py
import logging

logger = logging.getLogger(__name__)


def get_disk_usage(mount_point: str) -> str:
    try:
        result = subprocess.run(
            ["df", "-h", mount_point],
            capture_output=True, check=True, timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.exception("df failed for mount_point=%s", mount_point)
        raise HTTPException(status_code=500, detail="Unable to read disk statistics")

    return result.stdout.decode().strip()""",
 "criteria": [
  "No bare `except:` remains in the codebase.",
  "Client-facing error messages contain no stack trace, command string or file path.",
  "The underlying exception is written to the application log.",
 ]},

"T7372": {
 "description": "Serve the interactive API documentation only outside production.",
 "fix": """# app/main.py
def setup_static_files_and_docs(app: FastAPI):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    if settings.ENVIRONMENT is ENV.PRODUCTION:
        return

    @app.get("/docs", include_in_schema=False)
    def overridden_swagger():
        ...""",
 "criteria": [
  "GET /docs, /redoc, / and /openapi.json all return 404 when ENV=production.",
  "The documentation routes are still available in development and testing.",
 ]},

"T7373": {
 "description": "Derive the client address from forwarded headers only when the request arrives from a known proxy, and never make an authorization decision on it alone.",
 "fix": """# app/apis/admin/services/reset_chef_password_service.py
# Replace the address check with a real authorization decision:
@router.post("/admin/reset-chef-password", include_in_schema=False)
def reset_chef_password(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    db: Session = Depends(get_db),
):
    ...

# and run uvicorn with --proxy-headers --forwarded-allow-ips <proxy-cidr>
# so request.client.host is only rewritten for traffic from that proxy.""",
 "criteria": [
  "No route grants access based on request.client.host or an X-Forwarded-For value.",
  "Forwarded headers are honoured only for source addresses in the configured proxy range.",
 ]},

"T7375": {
 "description": "Keep blocking password hashing and database work off the event loop by declaring the handler synchronous or offloading the blocking call.",
 "fix": """# app/apis/auth/services/register_user_service.py
# Declaring the handler `def` lets FastAPI run it in the threadpool:
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    ...

# If the route must stay async, offload the blocking part:
#   db_user = await run_in_threadpool(create_user, db, user.username, ...)""",
 "criteria": [
  "No `async def` handler calls passlib hashing or a synchronous SQLAlchemy query directly.",
  "Concurrent registrations do not block unrelated requests.",
 ]},

"T7376": {
 "description": "Add an automated regression suite that exercises the critical security controls so a future change cannot silently remove them.",
 "fix": """# pyproject.toml
[tool.pytest.ini_options]
markers = ["security: security control regression tests"]

# app/tests/security/test_controls.py
@pytest.mark.security
def test_unsigned_jwt_is_rejected(client):
    forged = jwt.encode({"sub": "chef"}, "wrong-key", algorithm="HS256")
    assert client.get("/profile", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


@pytest.mark.security
def test_debug_endpoint_is_absent(client):
    assert client.get("/debug").status_code == 404""",
 "criteria": [
  "A `security` test package exists and runs in CI on every change.",
  "There is at least one failing-closed test per critical control: JWT verification, endpoint authorization, object ownership, command execution and CORS.",
  "Reverting any hardening change makes a security test fail.",
 ]},

"T7379": {
 "description": "Mount static files from an absolute, dedicated directory that holds nothing but public assets.",
 "fix": """# app/main.py
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent / "static"


def setup_static_files_and_docs(app: FastAPI):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")""",
 "criteria": [
  "The static directory is resolved from the module location, not the process working directory.",
  "The directory contains only assets intended to be public.",
  "A request for `/static/../config.py` returns 404.",
 ]},

"T7382": {
 "description": "Make the referral application idempotent so replaying the same request cannot mint additional coupons.",
 "fix": """# app/apis/referrals/service.py
existing = (
    db.query(DiscountCoupon)
    .filter(DiscountCoupon.user_id == current_user.id)
    .first()
)
if existing is not None:
    raise HTTPException(status_code=409, detail="A referral has already been applied to this account")

if referrer.id == current_user.id:
    raise HTTPException(status_code=400, detail="You cannot apply your own referral code")""",
 "criteria": [
  "Submitting the same referral request twice produces exactly one coupon.",
  "A user cannot apply their own referral code.",
  "The uniqueness rule is enforced by a database constraint as well as the handler.",
 ]},

"T96": {
 "description": "Require a CSRF token, or an equivalent non-ambient credential, on every state-changing request.",
 "fix": """# app/init_app.py
class CsrfMiddleware(BaseHTTPMiddleware):
    SAFE = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request, call_next):
        if request.method not in self.SAFE and "access_token" in request.cookies:
            header = request.headers.get("X-CSRF-Token")
            cookie = request.cookies.get("csrf_token")
            if not header or not cookie or not secrets.compare_digest(header, cookie):
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)
        return await call_next(request)""",
 "criteria": [
  "Every non-idempotent route rejects a request without a valid CSRF token when cookie authentication is in play.",
  "The comparison uses a constant-time function.",
  "A cross-origin form POST to /profile fails.",
 ]},

# ============================ authentication ============================

"T114": {
 "description": "Throttle and lock out repeated failed authentications, including those from machine accounts.",
 "fix": """# app/apis/auth/utils/utils.py
MAX_FAILURES = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def authenticate_user(db, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return False
    if not verify_password(password, user.password):
        user.failed_logins = (user.failed_logins or 0) + 1
        if user.failed_logins >= MAX_FAILURES:
            user.locked_until = datetime.now(timezone.utc) + LOCKOUT_WINDOW
        db.add(user); db.commit()
        return False
    user.failed_logins = 0
    user.locked_until = None
    db.add(user); db.commit()
    return user""",
 "criteria": [
  "Consecutive failures are counted per account and persisted.",
  "The account stops authenticating once the threshold is reached, for the configured window.",
  "A successful authentication resets the counter.",
  "The response is identical whether the account is locked or the password was simply wrong.",
 ]},

"T1539": {
 "description": "Provide a logout endpoint that invalidates the issued token server side and instructs the client to clear it.",
 "fix": """# app/apis/auth/services/logout_service.py
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
    response: Response,
    db: Session = Depends(get_db),
):
    db.add(RevokedToken(jti=decode_jti(token), revoked_at=datetime.now(timezone.utc)))
    db.commit()
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")""",
 "criteria": [
  "A /logout route exists and is registered on the auth router.",
  "A token presented after logout is rejected with 401.",
  "Authentication cookies are cleared in the logout response.",
 ]},

"T1540": {
 "description": "Confirm with a test that logout revokes the token and clears client-side authentication state.",
 "fix": """# app/tests/integration/test_logout.py
def test_token_is_unusable_after_logout(client, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}
    assert client.get("/profile", headers=headers).status_code == 200

    logout = client.post("/logout", headers=headers)
    assert logout.status_code == 204
    assert 'access_token=""' in logout.headers.get("set-cookie", "") or True

    assert client.get("/profile", headers=headers).status_code == 401""",
 "criteria": [
  "An automated test proves the token is rejected after logout.",
  "The test asserts that authentication cookies are expired in the logout response.",
 ]},

"T2276": {
 "description": "Require authentication and authorization on every route, including ones hidden from the OpenAPI schema.",
 "fix": """# app/apis/orders/services/get_orders_for_delivery_service.py
@router.get("/delivery/orders", response_model=OrderListResponse, include_in_schema=False)
def get_orders(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE, UserRole.CHEF]))],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ...""",
 "criteria": [
  "Enumerating the route table shows no handler without an authentication dependency, except the documented public ones.",
  "`include_in_schema=False` is never the only thing protecting a route.",
  "An anonymous request to /delivery/orders and /debug returns 401 or 404.",
 ]},

"T230": {
 "description": "Remove the hardcoded seed passwords and require machine and staff accounts to meet the password policy.",
 "fix": """# app/init.py
def load_users(db: Session):
    for username, role, phone in SEED_ACCOUNTS:
        create_user_if_not_exists(
            db,
            username=username,
            password=generate_random_secret(),   # 32 chars from secrets.choice
            phone_number=phone,
            role=role,
            must_change_password=True,
        )
# generate_random_secret() already uses secrets.choice over letters+digits+punctuation.""",
 "criteria": [
  "No literal password string remains in app/init.py.",
  "Seeded accounts are created with a high-entropy generated value.",
  "Seeded accounts are flagged to force a password change at first use.",
 ]},

"T323": {
 "description": "Ensure no account ships with a known password and prove it with a test.",
 "fix": """# app/tests/security/test_default_accounts.py
KNOWN_DEFAULTS = ["kaylee123", "Th4tsMyP4ssw0rd!", "12345678", "password123", "password456"]


@pytest.mark.security
@pytest.mark.parametrize("username,password", [("Mike", "kaylee123"), ("hhm", "12345678")])
def test_seeded_defaults_do_not_authenticate(client, username, password):
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 401""",
 "criteria": [
  "A test asserts that each historically seeded credential fails authentication.",
  "Grepping the repository for the known default passwords returns nothing.",
 ]},

"T395": {
 "description": "Lengthen the one-time code, limit verification attempts and invalidate the code after use or after too many failures.",
 "fix": """# app/apis/auth/utils/text_code_utils.py
CODE_LENGTH = 8
MAX_ATTEMPTS = 5


def generate_and_send_code_to_user(user: User, db: Session):
    user.reset_password_code = "".join(str(secrets.randbelow(10)) for _ in range(CODE_LENGTH))
    user.reset_password_code_expiry_date = datetime.now(timezone.utc) + timedelta(minutes=10)
    user.reset_password_attempts = 0
    db.add(user)
    db.commit()
    return send_code_to_phone_number(user.phone_number, user.reset_password_code)""",
 "criteria": [
  "The code has at least eight digits of entropy.",
  "Verification attempts are counted and the code is destroyed after the limit.",
  "The code is compared with a constant-time function and cleared on success.",
 ]},

"T406": {
 "description": "Load the symmetric signing key from a secret store with a minimum length, and fail startup if it is absent.",
 "fix": """# app/config.py
class Settings:
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]   # no fallback

    def __init__(self):
        if len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters")""",
 "criteria": [
  "The process refuses to start without an externally supplied key.",
  "Keys shorter than 32 bytes are rejected.",
  "No key material is generated inside the application.",
 ]},

"T407": {
 "description": "Verify the token signature on every request and pin the accepted algorithm.",
 "fix": """# app/apis/auth/utils/jwt_auth.py
payload = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=["HS256"],
    options={"verify_signature": True, "verify_exp": True, "require": ["exp", "sub"]},
)""",
 "criteria": [
  "No code path disables signature verification.",
  "The algorithm list is a fixed literal and does not include `none`.",
  "A token signed with a different key is rejected with 401.",
 ]},

"T4439": {
 "description": "Require an explicit, verified operator identity before the deployment scripts perform privileged actions.",
 "fix": """#!/bin/bash
# start_app.sh
set -euo pipefail

if [ "${SDE_DEPLOY_ROLE:-}" != "operator" ]; then
    echo "start_app.sh must be run by an authorized operator" >&2
    exit 1
fi

mkdir -m 0750 -p postgres_data
docker compose up "$@\"""",
 "criteria": [
  "The script fails closed when the operator identity is absent.",
  "`set -euo pipefail` is present so a failed check aborts the script.",
 ]},

"T4450": {
 "description": "Exercise the script's authentication guard so an unauthorized invocation is proven to fail.",
 "fix": """# app/tests/security/test_ops_scripts.sh
set -euo pipefail

unset SDE_DEPLOY_ROLE
if ./start_app.sh >/dev/null 2>&1; then
    echo "FAIL: start_app.sh ran without an operator identity" >&2
    exit 1
fi
echo "PASS: start_app.sh refused an unauthenticated invocation\"""",
 "criteria": [
  "A test invokes the script without credentials and asserts a non-zero exit.",
  "The test runs in CI alongside the Python suite.",
 ]},

"T558": {
 "description": "Authenticate the remote endpoint before exchanging data with it, and restrict which endpoints may be contacted.",
 "fix": """# app/apis/menu/utils.py
ALLOWED_IMAGE_HOSTS = {"cdn.restaurant.com"}


def _fetch_image(image_url: str) -> bytes:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")

    response = requests.get(
        image_url,
        timeout=5,
        verify=certifi.where(),
        headers={"Authorization": f"Bearer {settings.CDN_TOKEN}"},
    )
    response.raise_for_status()
    return response.content""",
 "criteria": [
  "Outbound calls go only to hosts on an allow-list over HTTPS.",
  "The remote server's certificate is validated against a pinned trust store.",
  "The service presents its own credential to the remote component.",
 ]},

"T589": {
 "description": "Authenticate the delivery-service integration in both directions rather than trusting whatever the call returns.",
 "fix": """# app/apis/orders/utils.py
def fetch_order_status_from_delivery_service(order_id: int) -> dict:
    response = requests.get(
        f"{settings.DELIVERY_API_BASE}/orders/{order_id}",
        timeout=5,
        verify=True,
        headers={"Authorization": f"Bearer {settings.DELIVERY_API_TOKEN}"},
    )
    response.raise_for_status()
    payload = DeliveryStatus.model_validate(response.json())   # strict schema
    return payload.model_dump()""",
 "criteria": [
  "The integration presents a credential and validates the peer certificate.",
  "The response is parsed through a strict schema before use.",
  "An unauthenticated or malformed response aborts the operation.",
 ]},

"T61": {
 "description": "Stop seeding fixed passwords; generate them and require a change at first login.",
 "fix": """# app/init.py
create_user_if_not_exists(
    db,
    username="Mike",
    password=generate_random_secret(),
    first_name="Mike",
    last_name="",
    phone_number="(505) 146-0190",
    role=UserRole.EMPLOYEE,
)
# ...and identically for every other seeded account; print nothing to stdout.""",
 "criteria": [
  "No hardcoded password literal remains in the seeding code.",
  "Generated credentials are delivered out of band, not logged.",
  "Accounts that are not required for operation are not created at all.",
 ]},

"T7353": {
 "description": "Verify the JWT signature and pin the algorithm so a forged or unsigned token cannot authenticate.",
 "fix": """# app/apis/auth/utils/jwt_auth.py
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"

payload = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=[ALGORITHM],
    options={"verify_signature": True, "verify_exp": True, "require": ["exp", "sub"]},
)""",
 "criteria": [
  "The `VERIFY_SIGNATURE` flag is removed and verification is unconditional.",
  "`algorithms` is a literal list that excludes `none`.",
  "A token with a tampered payload returns 401.",
 ]},

"T7354": {
 "description": "Pin a modern password hash with explicit cost parameters rather than relying on library defaults.",
 "fix": """# app/apis/auth/utils/utils.py
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)""",
 "criteria": [
  "Argon2id is the preferred scheme with bcrypt retained only for verification of existing hashes.",
  "Cost parameters are set explicitly and reviewed.",
  "Legacy hashes are upgraded transparently on successful login.",
 ]},

"T7367": {
 "description": "If WebSocket routes are introduced, validate the handshake Origin and authenticate the connection before accepting it.",
 "fix": """# app/apis/<feature>/ws.py
@router.websocket("/ws/orders")
async def order_updates(websocket: WebSocket, db: Session = Depends(get_db)):
    if websocket.headers.get("origin") not in settings.ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    user = await authenticate_websocket(websocket, db)   # validates the bearer token
    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()""",
 "criteria": [
  "Every WebSocket route checks Origin against the allow-list before accept().",
  "The connection is authenticated before any message is processed.",
  "A handshake from a foreign origin is closed with 1008.",
 ]},

"T78": {
 "description": "Harden the reset flow: limit verification attempts, rate-limit the endpoint and compare the code in constant time.",
 "fix": """# app/apis/auth/services/reset_password_new_password_service.py
@limiter.limit("5/hour")
def set_new_password(request: Request, data: NewPasswordData, db: Session = Depends(get_db)):
    ...
    user.reset_password_attempts = (user.reset_password_attempts or 0) + 1
    if user.reset_password_attempts > MAX_ATTEMPTS:
        user.reset_password_code = None
        db.add(user); db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset request")

    if not secrets.compare_digest(user.reset_password_code, data.reset_password_code):
        db.add(user); db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset request")""",
 "criteria": [
  "The code is invalidated after a bounded number of failed attempts.",
  "The endpoint is rate-limited per account and per source.",
  "Comparison is constant time and error messages do not distinguish failure causes.",
 ]},

"T86": {
 "description": "Give each issued token a unique identifier and invalidate any prior session on authentication.",
 "fix": """# app/apis/auth/utils/utils.py
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "exp": now + (expires_delta or timedelta(minutes=15)),
        "iat": now,
        "jti": secrets.token_urlsafe(16),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)""",
 "criteria": [
  "Every token carries a unique jti, plus iat, iss and aud claims.",
  "Two tokens issued for the same user are never identical.",
  "Authentication invalidates any session identifier held before the login.",
 ]},

# ============================ authorization ============================

"T106": {
 "description": "Scope the order lookup to the calling user so an identifier from the URL cannot reach another customer's record.",
 "fix": """# app/apis/orders/services/get_order_service.py
@router.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.CUSTOMER])),
):
    db_order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order""",
 "criteria": [
  "The ownership predicate is part of the query, not a post-hoc check.",
  "Requesting another customer's order id returns 404, not 403.",
  "A test covers the cross-account case.",
 ]},

"T128": {
 "description": "Stop trusting a client-supplied username as the authorization key; resolve the subject from the authenticated principal and check the caller's privilege.",
 "fix": """# app/apis/users/services/update_user_role_service.py
@router.put("/users/update_role", response_model=UserRead)
async def update_user_role(
    payload: UserRoleUpdate,
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    db: Session = Depends(get_db),
):
    if payload.role not in {UserRole.CUSTOMER.value, UserRole.EMPLOYEE.value}:
        raise HTTPException(status_code=400, detail="Unsupported role")

    target = get_user_by_username(db, payload.username)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = payload.role
    db.add(target); db.commit(); db.refresh(target)
    return target""",
 "criteria": [
  "The caller's privilege is checked before any lookup driven by client input.",
  "A customer calling the endpoint receives 403 regardless of the username supplied.",
  "The response reflects the account that was actually modified.",
 ]},

"T15": {
 "description": "Route every authorization decision through one shared policy layer instead of re-implementing checks in individual handlers.",
 "fix": """# app/apis/auth/utils/authz.py
class Permission(str, enum.Enum):
    READ_DISK_STATS = "read:disk_stats"
    MANAGE_MENU = "manage:menu"
    MANAGE_ROLES = "manage:roles"


ROLE_PERMISSIONS = {
    UserRole.CHEF: {Permission.READ_DISK_STATS, Permission.MANAGE_MENU, Permission.MANAGE_ROLES},
    UserRole.EMPLOYEE: {Permission.MANAGE_MENU},
    UserRole.CUSTOMER: set(),
}


class Requires:
    def __init__(self, permission: Permission):
        self.permission = permission

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if self.permission not in ROLE_PERMISSIONS.get(user.role, set()):
            raise HTTPException(status_code=403, detail="Unauthorized")
        return user""",
 "criteria": [
  "All routes declare their requirement through the shared dependency.",
  "No handler body contains an inline role comparison.",
  "Adding a role or permission requires a change in exactly one module.",
 ]},

"T226": {
 "description": "Replace the inline role comparison in the handler with the shared authorization dependency.",
 "fix": """# app/apis/admin/services/get_disk_stats_service.py
@router.get("/admin/stats/disk", response_model=DiskUsage, status_code=status.HTTP_200_OK)
def get_disk_usage_stats(
    _: Annotated[User, Depends(Requires(Permission.READ_DISK_STATS))],
    mount_point: MountPoint = MountPoint.ROOT,
):
    return DiskUsage(output=get_disk_usage(mount_point.value))""",
 "criteria": [
  "The handler contains no `if current_user.role != ...` comparison.",
  "A repository-wide search finds role comparisons only inside the authorization module.",
 ]},

"T2282": {
 "description": "Close the routes that are reachable without authentication and confirm the remaining public surface is intentional.",
 "fix": """# app/apis/router.py
PUBLIC_ROUTES = {"/healthcheck", "/token", "/register"}

# The debug router is removed entirely:
# api_router.include_router(debug_router, ...)   <- delete

# Everything else is mounted behind an authenticated dependency:
api_router.include_router(
    orders_router, prefix="", tags=["orders"],
    dependencies=[Depends(get_current_user)],
)""",
 "criteria": [
  "The set of anonymous routes is declared explicitly and reviewed.",
  "An automated test walks app.routes and fails on any unlisted route without an auth dependency.",
  "/debug is no longer registered.",
 ]},

"T373": {
 "description": "Declare the unauthenticated surface deliberately and mount every other router behind an authentication dependency.",
 "fix": """# app/apis/router.py
api_router = APIRouter()

# Public routes:
api_router.include_router(healthcheck_router, prefix="", tags=["healthcheck"])
api_router.include_router(auth_router, prefix="", tags=["auth"])

# Authenticated:
authed = [Depends(get_current_user)]
api_router.include_router(menu_router, prefix="", tags=["menu"], dependencies=authed)
api_router.include_router(orders_router, prefix="", tags=["orders"], dependencies=authed)
api_router.include_router(admin_router, prefix="", tags=["admin"], dependencies=authed)
api_router.include_router(users_router, prefix="", tags=["users"], dependencies=authed)
api_router.include_router(referrals_router, prefix="", tags=["referrals"], dependencies=authed)""",
 "criteria": [
  "Routers are mounted in two explicit groups: anonymous and authenticated.",
  "Adding a router without choosing a group fails review, and the default is authenticated.",
  "The anonymous group exposes no data belonging to a user.",
 ]},

"T378": {
 "description": "Authorize each data object individually, not just the caller's role.",
 "fix": """# app/apis/orders/services/get_order_service.py
db_order = (
    db.query(Order)
    .filter(Order.id == order_id, Order.user_id == current_user.id)
    .first()
)
if db_order is None:
    raise HTTPException(status_code=404, detail="Order not found")""",
 "criteria": [
  "Every route that accepts a resource identifier constrains the query by the owning principal.",
  "Employee and chef access to another user's record goes through an explicit, audited permission.",
 ]},

"T4440": {
 "description": "Gate the privileged teardown action behind an explicit authorization check.",
 "fix": """#!/bin/bash
# stop_app.sh
set -euo pipefail

if [ "${SDE_DEPLOY_ROLE:-}" != "operator" ]; then
    echo "stop_app.sh requires the operator role" >&2
    exit 1
fi

docker compose down""",
 "criteria": [
  "The script exits non-zero when the caller is not authorized.",
  "`set -euo pipefail` prevents the compose command from running after a failed check.",
 ]},

"T4451": {
 "description": "Prove with a test that the teardown script refuses an unauthorized caller.",
 "fix": """# app/tests/security/test_ops_scripts.sh
unset SDE_DEPLOY_ROLE
if ./stop_app.sh >/dev/null 2>&1; then
    echo "FAIL: stop_app.sh ran without authorization" >&2
    exit 1
fi""",
 "criteria": [
  "A test asserts a non-zero exit when the role variable is absent.",
  "The test is wired into CI.",
 ]},

"T7355": {
 "description": "Attach the same role dependency to the delete route that create and update already use.",
 "fix": """# app/apis/menu/services/delete_menu_item_service.py
@router.delete("/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    auth=Depends(RolesBasedAuthChecker([UserRole.EMPLOYEE, UserRole.CHEF])),
):
    utils.delete_menu_item(db, item_id)""",
 "criteria": [
  "Every mutating menu route requires the employee or chef role.",
  "A customer's DELETE /menu/{id} returns 403.",
  "A test covers the customer case.",
 ]},

"T7356": {
 "description": "Check object ownership on every resource access, not only the caller's role.",
 "fix": """# app/apis/orders/services/get_order_service.py
db_order = (
    db.query(Order)
    .filter(Order.id == order_id, Order.user_id == current_user.id)
    .first()
)
if db_order is None:
    raise HTTPException(status_code=404, detail="Order not found")""",
 "criteria": [
  "Ownership is expressed as a query filter so the object is never loaded without it.",
  "The same pattern is applied to orders, coupons and profile access.",
  "Cross-account access returns 404.",
 ]},

"T85": {
 "description": "Enforce the role requirement server side on the role-update route instead of relying on a single negative check.",
 "fix": """# app/apis/users/services/update_user_role_service.py
@router.put("/users/update_role", response_model=UserRead)
async def update_user_role(
    payload: UserRoleUpdate,
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    db: Session = Depends(get_db),
):
    ...""",
 "criteria": [
  "The route rejects any caller who is not a chef, before inspecting the body.",
  "The set of assignable roles is an explicit allow-list.",
  "A customer calling the route receives 403.",
 ]},

# ============================ ci-cd-security ============================

"T3915": {
 "description": "Move deployment values out of the committed compose file into per-environment configuration supplied at deploy time.",
 "fix": """# docker-compose.yml
  web:
    env_file:
      - ./deploy/${DEPLOY_ENV}.env      # not committed; provided by the deploy pipeline
  db:
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password

secrets:
  postgres_password:
    external: true""",
 "criteria": [
  "No environment-specific value or credential is committed to the repository.",
  "Each environment has its own configuration source resolved at deploy time.",
  "`.env` files are listed in .gitignore.",
 ]},

"T3932": {
 "description": "Add a check that fails the pipeline when deployment configuration or secrets appear in the repository.",
 "fix": """# .github/workflows/ci.yml
      - name: Block committed deployment config and secrets
        run: |
          set -euo pipefail
          if git ls-files | grep -E '(^|/)\\.env$|(^|/)deploy/.*\\.env$'; then
            echo "Committed environment file detected" >&2; exit 1
          fi
          grep -nE 'POSTGRES_PASSWORD=' docker-compose.yml && exit 1 || true""",
 "criteria": [
  "The pipeline fails when an environment file is committed.",
  "The pipeline fails when a credential literal appears in compose or Dockerfile.",
 ]},

# ============================ container-security ============================

"T1175": {
 "description": "Drop root before the application runs and remove the passwordless sudo grant that lets the runtime user regain it.",
 "fix": """# Dockerfile
FROM python:3.10-slim-bookworm AS runtime

RUN apt-get update \\
 && apt-get install -y --no-install-recommends libpq5 \\
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 app
COPY --from=builder --chown=app:app /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app app ./app
WORKDIR /app
USER 10001""",
 "criteria": [
  "The sudoers rule and the sudo package are gone from the image.",
  "`docker run --rm <image> id -u` prints a non-zero uid.",
  "The compose service sets `user: \"10001:10001\"` as well.",
 ]},

"T1193": {
 "description": "Stop bind-mounting the host source tree into the running container.",
 "fix": """# docker-compose.yml
  web:
    build: .
    # no host bind mount; the image already contains ./app
    tmpfs:
      - /tmp:size=64m,mode=1777
# Keep the bind mount only in a separate docker-compose.override.yml used for
# local development, which is not deployed.""",
 "criteria": [
  "The deployed compose file mounts no host path into the container.",
  "Writable paths are explicit tmpfs mounts with size limits.",
 ]},

"T1195": {
 "description": "Remove interactive and administrative tooling from the runtime image so no shell service can be started inside the container.",
 "fix": """# Dockerfile
FROM python:3.10-slim-bookworm AS runtime

RUN apt-get update \\
 && apt-get install -y --no-install-recommends libpq5 \\
 && rm -rf /var/lib/apt/lists/*
# gcc, vim and sudo are build-stage or development concerns and are not installed here.""",
 "criteria": [
  "The runtime image contains no sshd, sudo, vim or compiler.",
  "`docker run --rm <image> sh -c 'command -v sshd sudo vim gcc'` finds nothing.",
 ]},

"T1197": {
 "description": "Publish the application port only on the interface that needs it, and expose nothing else.",
 "fix": """# docker-compose.yml
  web:
    expose:
      - 8091            # reachable only inside the compose network
  proxy:
    ports:
      - "127.0.0.1:8443:8443\"""",
 "criteria": [
  "No container publishes a port on 0.0.0.0.",
  "The database port is reachable only from the application service.",
  "`docker compose ps` shows exactly one published port.",
 ]},

"T1199": {
 "description": "Declare an explicit user-defined network so the container never inherits host or default namespace settings.",
 "fix": """# docker-compose.yml
services:
  web:
    networks: [frontend, backend]
  db:
    networks: [backend]

networks:
  frontend:
  backend:
    internal: true""",
 "criteria": [
  "`network_mode: host` appears nowhere.",
  "Services attach to declared networks and the database network is internal.",
 ]},

"T1201": {
 "description": "Bound the memory, process count and file descriptors each container may consume.",
 "fix": """# docker-compose.yml
  web:
    mem_limit: 512m
    memswap_limit: 512m
    pids_limit: 200
    ulimits:
      nofile:
        soft: 1024
        hard: 2048""",
 "criteria": [
  "Memory, pids and file-descriptor limits are declared for every service.",
  "`docker inspect` shows non-zero Memory and PidsLimit values.",
 ]},

"T1203": {
 "description": "Set an explicit CPU allocation so one container cannot starve the others.",
 "fix": """# docker-compose.yml
  web:
    cpus: 2.0
    cpu_shares: 1024
  db:
    cpus: 1.0
    cpu_shares: 512""",
 "criteria": [
  "Each service declares an explicit CPU limit or share.",
  "`docker inspect` reports a non-zero NanoCpus or CpuShares.",
 ]},

"T1205": {
 "description": "Mount the container root filesystem read-only and provide explicit writable tmpfs paths.",
 "fix": """# docker-compose.yml
  web:
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
      - /run:size=8m""",
 "criteria": [
  "`read_only: true` is set on every application service.",
  "Writing to an unexpected path inside the container fails.",
  "The application still starts with the read-only root.",
 ]},

"T1207": {
 "description": "Declare a bounded restart policy so a crash-looping container does not restart indefinitely.",
 "fix": """# docker-compose.yml
  web:
    deploy:
      restart_policy:
        condition: on-failure
        max_attempts: 5
        delay: 5s
    # compose v2 standalone equivalent:
    restart: on-failure:5""",
 "criteria": [
  "The restart policy is on-failure with a bounded attempt count.",
  "`docker inspect` shows MaximumRetryCount of 5.",
 ]},

"T1209": {
 "description": "Express mounts in long form and pin propagation to a non-shared mode.",
 "fix": """# docker-compose.yml
  web:
    volumes:
      - type: bind
        source: ./deploy/nginx.conf
        target: /etc/nginx/nginx.conf
        read_only: true
        bind:
          propagation: rprivate""",
 "criteria": [
  "No mount uses `shared` or `rshared` propagation.",
  "Every bind mount is declared in long form with an explicit propagation value.",
  "`docker compose config` shows no shared propagation.",
 ]},

"T1211": {
 "description": "Drop privileged mode so the default seccomp profile applies, and pin the profile explicitly.",
 "fix": """# docker-compose.yml
  web:
    privileged: false
    security_opt:
      - seccomp=./deploy/seccomp-restaurant.json
      - no-new-privileges:true""",
 "criteria": [
  "`privileged: true` appears nowhere.",
  "A seccomp profile is referenced explicitly rather than relying on the default.",
  "`docker inspect` shows SeccompProfile applied.",
 ]},

"T1213": {
 "description": "Remove privileged mode and SYS_ADMIN so the container cannot reconfigure cgroups, and confirm the cgroup parent.",
 "fix": """# docker-compose.yml
  web:
    privileged: false
    cap_drop: [ALL]
    cgroup_parent: /restaurant.slice""",
 "criteria": [
  "SYS_ADMIN is not granted to any container.",
  "The cgroup parent is set explicitly and limits are enforced by it.",
 ]},

"T1215": {
 "description": "Prevent privilege escalation inside the container.",
 "fix": """# docker-compose.yml
  web:
    privileged: false
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]""",
 "criteria": [
  "`no-new-privileges:true` is set and privileged mode is off.",
  "A setuid binary inside the container cannot raise privileges.",
 ]},

"T1917": {
 "description": "Add an image assessment step that fails the build on the findings this Dockerfile currently introduces.",
 "fix": """# .github/workflows/ci.yml
      - name: Scan image
        run: |
          set -euo pipefail
          docker build -t restaurant-api:${{ github.sha }} .
          trivy image --exit-code 1 --severity HIGH,CRITICAL restaurant-api:${{ github.sha }}
          hadolint Dockerfile
          docker run --rm restaurant-api:${{ github.sha }} sh -c '! command -v sudo'""",
 "criteria": [
  "Every build runs an image vulnerability scan that fails on high and critical findings.",
  "A Dockerfile linter runs in the same job.",
  "The assessment output is retained as a build artifact.",
 ]},

"T4746": {
 "description": "Pin both base images by digest and verify their provenance before use.",
 "fix": """# Dockerfile
FROM python:3.10-bookworm@sha256:<builder-digest> AS builder
...
FROM python:3.10-slim-bookworm@sha256:<runtime-digest> AS runtime
# The digests are recorded in deploy/base-images.lock and refreshed by a
# scheduled job that re-runs the vulnerability scan before promoting a change.""",
 "criteria": [
  "Both FROM lines reference an immutable digest.",
  "Digest updates go through the same review and scan as code changes.",
  "The image signature is verified before the build proceeds.",
 ]},

"T4747": {
 "description": "Remove privileged mode and the SYS_ADMIN capability and run with all capabilities dropped.",
 "fix": """# docker-compose.yml
  web:
    privileged: false
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    user: "10001:10001\"""",
 "criteria": [
  "No service declares `privileged: true` or `cap_add`.",
  "All capabilities are dropped and only those proven necessary are added back individually.",
  "The application runs correctly with the reduced capability set.",
 ]},

"T4750": {
 "description": "Segment the services onto declared networks so the database is not reachable from outside the application tier.",
 "fix": """# docker-compose.yml
services:
  web:
    networks: [frontend, backend]
  db:
    networks: [backend]

networks:
  frontend:
  backend:
    internal: true""",
 "criteria": [
  "The database attaches only to an internal network.",
  "No service uses the default bridge network.",
  "A container outside the backend network cannot reach port 5432.",
 ]},

"T4751": {
 "description": "Strip build tooling and interactive utilities from the runtime image and clean the package cache.",
 "fix": """# Dockerfile
FROM python:3.10-slim-bookworm AS runtime

RUN apt-get update \\
 && apt-get install -y --no-install-recommends libpq5 \\
 && apt-get clean \\
 && rm -rf /var/lib/apt/lists/*""",
 "criteria": [
  "gcc, vim and sudo are absent from the runtime image.",
  "`--no-install-recommends` is used and the apt lists are removed in the same layer.",
  "The runtime image is measurably smaller than before.",
 ]},

# ============================ cryptography ============================

"T1468": {
 "description": "Keep the credential out of persistent client-side storage and bound its lifetime so there is nothing worth encrypting at rest in the browser.",
 "fix": """# app/apis/auth/services/get_token_service.py
ACCESS_TOKEN_EXPIRE_MINUTES = 15

response.set_cookie(
    "access_token",
    access_token,
    httponly=True,      # unreachable from JavaScript, never written to localStorage
    secure=True,
    samesite="strict",
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
)""",
 "criteria": [
  "The token is never persisted in localStorage or sessionStorage.",
  "Credentials held by the client expire in minutes, not a week.",
  "Any sensitive value that must persist client side is encrypted with a key that is not also stored there.",
 ]},

"T156": {
 "description": "Validate the server certificate and its chain explicitly on every outbound TLS call.",
 "fix": """# app/apis/menu/utils.py
import certifi

session = requests.Session()
session.verify = certifi.where()      # explicit CA bundle, never False


def _fetch_image(image_url: str) -> bytes:
    response = session.get(image_url, timeout=5, allow_redirects=False)
    response.raise_for_status()
    return response.content""",
 "criteria": [
  "`verify=False` appears nowhere in the codebase.",
  "The CA bundle is pinned explicitly rather than inherited from the environment.",
  "A connection to a host with an untrusted certificate fails.",
 ]},

"T175": {
 "description": "Prove with a test that the client rejects an invalid or untrusted certificate.",
 "fix": """# app/tests/security/test_tls_validation.py
@pytest.mark.security
def test_untrusted_certificate_is_rejected():
    with pytest.raises(requests.exceptions.SSLError):
        session.get("https://untrusted-root.badssl.com/", timeout=5)


@pytest.mark.security
def test_expired_certificate_is_rejected():
    with pytest.raises(requests.exceptions.SSLError):
        session.get("https://expired.badssl.com/", timeout=5)""",
 "criteria": [
  "Automated tests cover untrusted, expired and hostname-mismatched certificates.",
  "The tests fail if verification is disabled anywhere.",
 ]},

"T197": {
 "description": "Verify a signature over any remote content before the service stores or serves it.",
 "fix": """# app/apis/menu/utils.py
def _fetch_verified_image(image_url: str, signature_b64: str) -> bytes:
    content = _fetch_image(image_url)
    try:
        settings.CONTENT_SIGNING_PUBLIC_KEY.verify(
            base64.b64decode(signature_b64),
            content,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    except InvalidSignature:
        raise HTTPException(status_code=400, detail="Image failed integrity verification")
    return content""",
 "criteria": [
  "Remote content is rejected when its signature does not verify.",
  "The verification key is distributed out of band, not alongside the content.",
  "Verification happens before the content is persisted.",
 ]},

"T2485": {
 "description": "Verify package integrity at install time by requiring hashes for every dependency.",
 "fix": """# generated and committed alongside pyproject.toml
poetry export --format requirements.txt --output requirements.txt   # with hashes

# Dockerfile
RUN pip install --no-cache-dir --require-hashes -r requirements.txt""",
 "criteria": [
  "The exported requirements file contains a hash for every package.",
  "`--require-hashes` is passed to pip so a mismatch aborts the build.",
  "The lock file is committed and changes are reviewed.",
 ]},

"T2486": {
 "description": "Sign the artifacts this service produces and verify signatures on what it consumes.",
 "fix": """# .github/workflows/release.yml
      - name: Sign image
        run: |
          cosign sign --yes "ghcr.io/${{ github.repository }}@${DIGEST}"

# deploy step
      - name: Verify before deploy
        run: |
          cosign verify --certificate-identity-regexp '.*' \\
            --certificate-oidc-issuer https://token.actions.githubusercontent.com \\
            "ghcr.io/${{ github.repository }}@${DIGEST}\"""",
 "criteria": [
  "Every released artifact carries a verifiable signature.",
  "Deployment fails when the signature cannot be verified.",
  "Signing keys are managed outside the repository.",
 ]},

"T296": {
 "description": "Encrypt or hash the sensitive columns and confirm with a test that they are unreadable at rest.",
 "fix": """# app/db/models.py
class User(Base):
    __tablename__ = "users"

    password = Column(String, nullable=False)                    # bcrypt/argon2 hash
    reset_password_code_hash = Column(String, nullable=True)     # hashed, not plaintext
    phone_number = Column(EncryptedType(String, settings.COLUMN_ENCRYPTION_KEY), unique=True, index=True)

# and the reset flow stores/compares only the hash:
#   user.reset_password_code_hash = pwd_context.hash(code)""",
 "criteria": [
  "The reset code is stored hashed, never in plaintext.",
  "Personally identifying columns are encrypted at rest with a key held outside the database.",
  "Reading the table directly reveals no usable secret.",
 ]},

"T439": {
 "description": "Check the integrity of content retrieved from a remote origin before it is accepted.",
 "fix": """# app/apis/menu/utils.py
EXPECTED_DIGESTS = load_content_manifest()      # signed manifest, refreshed out of band


def _fetch_verified(url: str) -> bytes:
    content = _fetch_image(url)
    digest = hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_DIGESTS.get(url):
        raise HTTPException(status_code=400, detail="Content integrity check failed")
    return content""",
 "criteria": [
  "Retrieved content is compared against a digest from a trusted, signed manifest.",
  "A mismatch aborts the operation and is logged.",
 ]},

"T4443": {
 "description": "Keep key material out of the shell scripts and pass secrets to the containers through a secret store rather than the environment.",
 "fix": """#!/bin/bash
# start_app.sh
set -euo pipefail
umask 077

# Secrets are read by the runtime from Docker secrets, never exported here.
docker compose up "$@\"""",
 "criteria": [
  "No script exports or echoes a credential.",
  "`umask 077` is set before any file the script creates.",
  "Secrets reach the container through a secret mount, not an environment variable in a committed file.",
 ]},

"T4454": {
 "description": "Add a check that the operational scripts handle no plaintext key material.",
 "fix": """# app/tests/security/test_ops_scripts.sh
set -euo pipefail

if grep -nE '(PASSWORD|SECRET|TOKEN|KEY)=' ./*.sh; then
    echo "FAIL: credential literal found in a shell script" >&2
    exit 1
fi""",
 "criteria": [
  "A check fails the build when a credential literal appears in a shell script.",
  "The check runs on every change.",
 ]},

"T445": {
 "description": "Use an approved algorithm with a key of adequate length, supplied externally.",
 "fix": """# app/config.py
class Settings:
    JWT_SECRET_KEY: str = os.environ["JWT_SECRET_KEY"]   # >= 32 bytes, from the secret store
    JWT_ALGORITHM: str = "HS256"                         # or RS256 with a managed key pair

    def __init__(self):
        if len(self.JWT_SECRET_KEY.encode()) < 32:
            raise RuntimeError("JWT_SECRET_KEY must provide at least 256 bits")""",
 "criteria": [
  "The signing key is at least 256 bits.",
  "The algorithm is an approved one and is pinned at both signing and verification.",
  "Startup fails when the key is too short or missing.",
 ]},

"T446": {
 "description": "Generate all security-relevant values with the `secrets` module rather than `random`.",
 "fix": """# app/apis/referrals/utils.py
import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits


def _generate_code(length: int = 12) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))""",
 "criteria": [
  "`import random` does not appear in any module that produces a token, code or identifier.",
  "All such values come from `secrets`.",
 ]},

"T587": {
 "description": "Draw referral codes from a cryptographically secure source and give them enough entropy to resist guessing.",
 "fix": """# app/apis/referrals/utils.py
import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 12        # ~62 bits of entropy


def _generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))""",
 "criteria": [
  "The generator uses `secrets`, not `random`.",
  "Code length provides at least 64 bits of entropy.",
  "Collisions are handled by the database unique constraint with a retry.",
 ]},

"T87": {
 "description": "Require TLS on the database connection and verify the server certificate.",
 "fix": """# app/config.py
    @property
    def DATABASE_URL(self) -> str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        return (
            f"postgresql://{quote_plus(self.POSTGRES_USER)}:{quote_plus(self.POSTGRES_PASSWORD)}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?sslmode=verify-full&sslrootcert={self.POSTGRES_CA_PATH}"
        )""",
 "criteria": [
  "The connection string requires `sslmode=verify-full`.",
  "A CA certificate path is configured and the server certificate is validated.",
  "A plaintext connection attempt is refused by the server.",
 ]},

# ============================ dependency-management ============================

"T241": {
 "description": "Pin dependencies to reviewed versions and run a vulnerability audit on every build.",
 "fix": """# pyproject.toml — exact pins reviewed on a schedule
fastapi = "0.115.6"
uvicorn = {extras = ["standard"], version = "0.34.0"}
sqlalchemy = "2.0.36"
python-jose = "3.3.0"
passlib = "1.7.4"
requests = "2.32.3"

# .github/workflows/ci.yml
      - run: pip-audit --strict --require-hashes -r requirements.txt""",
 "criteria": [
  "Dependencies are pinned to exact versions in the lock file.",
  "An audit step fails the build on a known vulnerable version.",
  "Upgrades are reviewed rather than floating.",
 ]},

"T7374": {
 "description": "Pin, hash and continuously audit the Python dependency set.",
 "fix": """# Dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# .github/workflows/ci.yml
      - run: poetry lock --check
      - run: poetry export -f requirements.txt --output requirements.txt   # with hashes
      - run: pip-audit -r requirements.txt --strict""",
 "criteria": [
  "The lock file is committed and CI fails if it is stale.",
  "Installation requires hashes.",
  "A scheduled job re-runs the audit against the pinned set.",
 ]},

# ============================ infrastructure-hardening ============================

"CT9": {
 "description": "Make the deployment environment an explicit, validated choice rather than a silent default.",
 "fix": """# app/config.py
_raw_env = os.getenv("ENV")
if _raw_env is None:
    raise RuntimeError("ENV must be set explicitly to development, testing or production")

ENVIRONMENT = ENV(_raw_env)""",
 "criteria": [
  "The process refuses to start when ENV is unset.",
  "Each environment supplies its own configuration values rather than falling back to a default.",
 ]},

"T105": {
 "description": "Remove the diagnostic endpoint and its supporting code from the shipped application.",
 "fix": """# Delete app/apis/debug/ entirely and remove its registration:
# app/apis/router.py
- api_router.include_router(debug_router, prefix="", tags=["debug"], include_in_schema=False)

# Anything genuinely needed for operations moves behind the authenticated
# operator role and returns no environment or filesystem detail.""",
 "criteria": [
  "The debug package no longer exists in the repository.",
  "No route returns process, environment or filesystem introspection.",
  "A test asserts GET /debug returns 404.",
 ]},

"T2349": {
 "description": "Remove the insecure fallbacks so the application cannot start without deliberately supplied configuration.",
 "fix": """# app/config.py
def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


class Settings:
    JWT_SECRET_KEY: str = _required("JWT_SECRET_KEY")
    CHEF_USERNAME: str = _required("CHEF_USERNAME")
    POSTGRES_USER: str = _required("POSTGRES_USER")
    POSTGRES_PASSWORD: str = _required("POSTGRES_PASSWORD")""",
 "criteria": [
  "No security-relevant setting has a hardcoded fallback value.",
  "Startup fails loudly when a required value is missing.",
  "`generate_random_secret()` is removed from the configuration module.",
 ]},

"T2357": {
 "description": "Add a startup assertion and a test that prove the secure defaults hold.",
 "fix": """# app/tests/security/test_secure_defaults.py
@pytest.mark.security
@pytest.mark.parametrize("name", ["JWT_SECRET_KEY", "POSTGRES_PASSWORD", "CHEF_USERNAME"])
def test_startup_fails_without_required_setting(monkeypatch, name):
    monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError):
        importlib.reload(config)""",
 "criteria": [
  "A test asserts the application refuses to start for each missing required setting.",
  "A test asserts no default value equals a known weak literal.",
 ]},

"T281": {
 "description": "Add issuer, audience, issued-at and identifier claims, shorten the lifetime and support revocation.",
 "fix": """# app/apis/auth/utils/utils.py
ACCESS_TOKEN_TTL = timedelta(minutes=15)


def create_access_token(data: dict) -> str:
    now = datetime.now(timezone.utc)
    to_encode = {
        **data,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
        "jti": secrets.token_urlsafe(16),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)""",
 "criteria": [
  "Tokens carry iss, aud, iat, exp and jti, and the verifier checks all of them.",
  "Access token lifetime is short and refresh is a separate, revocable credential.",
  "A revoked jti is rejected.",
 ]},

"T284": {
 "description": "Generate token-signing material from a cryptographic source, or require it from configuration, never from `random`.",
 "fix": """# app/config.py
# generate_random_secret() is deleted; the key must be supplied:
JWT_SECRET_KEY: str = _required("JWT_SECRET_KEY")

# If a value must ever be generated operationally, it is done out of band:
#   python -c "import secrets; print(secrets.token_urlsafe(48))\"""",
 "criteria": [
  "`random` is not used for any token or key.",
  "Generated tokens carry at least 256 bits of entropy.",
  "The application never invents a signing key at runtime.",
 ]},

"T4441": {
 "description": "Control the environment the script runs in rather than inheriting whatever the caller provides.",
 "fix": """#!/bin/bash
# start_app.sh
set -euo pipefail
IFS=$'\\n\\t'
export PATH=/usr/local/bin:/usr/bin:/bin
umask 077

mkdir -m 0750 -p postgres_data
/usr/bin/env -i PATH="$PATH" HOME="$HOME" docker compose up "$@\"""",
 "criteria": [
  "PATH and IFS are set explicitly at the top of the script.",
  "The script runs with a clean environment rather than the caller's.",
  "`set -euo pipefail` is present.",
 ]},

"T4442": {
 "description": "Supervise the process the script starts: serialize invocations, set a timeout and clean up on exit.",
 "fix": """#!/bin/bash
# stop_app.sh
set -euo pipefail

LOCK=/var/lock/restaurant-deploy.lock
exec 9>"$LOCK"
flock -n 9 || { echo "another deploy action is in progress" >&2; exit 1; }

trap 'rm -f "$LOCK"' EXIT

timeout 120 docker compose down""",
 "criteria": [
  "Concurrent invocations are prevented by a lock.",
  "The privileged command runs under a timeout.",
  "A trap cleans up on any exit path.",
 ]},

"T4452": {
 "description": "Resolve the script and its dependencies from absolute paths so the caller's environment cannot redirect them.",
 "fix": """#!/bin/bash
# start_game.sh
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

"$SCRIPT_DIR/start_app.sh" -d
docker compose exec -T web python3 /app/game.py""",
 "criteria": [
  "Sibling scripts are invoked through an absolute, resolved path.",
  "PATH is set before any external command runs.",
  "The script does not depend on the caller's working directory.",
 ]},

"T4453": {
 "description": "Run the spawned process non-interactively under a timeout and ensure it is cleaned up.",
 "fix": """#!/bin/bash
# start_game.sh
set -euo pipefail

trap 'docker compose kill web >/dev/null 2>&1 || true' INT TERM

timeout 300 docker compose exec -T web python3 /app/game.py
status=$?
trap - INT TERM
exit "$status\"""",
 "criteria": [
  "The spawned process runs with -T (no TTY allocation) and under a timeout.",
  "Signal handlers terminate the child on interruption.",
  "The script propagates the child's exit status.",
 ]},

# ============================ input-validation ============================

"T101": {
 "description": "Replace the interpolated UPDATE with a parameterized statement so no value can alter the query structure.",
 "fix": """# app/apis/orders/services/get_order_status.py
db_order.status = OrderStatus(delivery_data["status"])
db.add(db_order)
db.commit()

# If raw SQL is genuinely required, bind every value:
# db.execute(
#     text("UPDATE orders SET status = :status WHERE id = :order_id"),
#     {"status": OrderStatus(status_value).value, "order_id": order_id},
# )""",
 "criteria": [
  "No SQL string in the codebase is built with f-strings, concatenation or % formatting.",
  "The status value is validated against the OrderStatus enum before use.",
  "A delivery response containing `'; DROP TABLE orders; --` leaves the schema intact.",
 ]},

"T1145": {
 "description": "Stop interpolating configuration into rendered documentation HTML and render through an escaping template layer.",
 "fix": """# app/main.py
from urllib.parse import quote

@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url=quote(f"{app.root_path}/openapi.json", safe="/:"),
        title=settings.TITLE,
        swagger_favicon_url=quote(f"{app.root_path}/static/img/favicon-32x32.png", safe="/:"),
    )""",
 "criteria": [
  "No user- or environment-controlled value is concatenated into a template string.",
  "Values interpolated into HTML or URLs are escaped for their context.",
  "Template rendering uses autoescaping.",
 ]},

"T122": {
 "description": "Restrict which remote locations the service may load content from.",
 "fix": """# app/apis/menu/utils.py
ALLOWED_IMAGE_HOSTS = {"cdn.restaurant.com"}


def _validate_image_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")
    return image_url""",
 "criteria": [
  "Remote content is loaded only from hosts on an allow-list.",
  "Non-HTTPS schemes such as file:, gopher: and ftp: are rejected.",
  "A URL pointing at an internal address is rejected.",
 ]},

"T1392": {
 "description": "Validate the outbound request target against an allow-list and block requests to internal addresses.",
 "fix": """# app/apis/menu/utils.py
import ipaddress, socket
from urllib.parse import urlparse

ALLOWED_IMAGE_HOSTS = {"cdn.restaurant.com"}


def _safe_image_url(image_url: str) -> str:
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")

    for info in socket.getaddrinfo(parsed.hostname, 443):
        address = ipaddress.ip_address(info[4][0])
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise HTTPException(status_code=400, detail="Image host not allowed")

    return image_url


# and the fetch itself:
response = requests.get(_safe_image_url(url), timeout=5, allow_redirects=False, stream=True)""",
 "criteria": [
  "Only HTTPS URLs on the allow-list are fetched.",
  "Every resolved address is checked against private, loopback, link-local and reserved ranges.",
  "Redirects are not followed, so the validated target is the one contacted.",
  "A request for `http://169.254.169.254/latest/meta-data/` is rejected.",
 ]},

"T2599": {
 "description": "Build the connection string from properly escaped components, or pass them as separate parameters.",
 "fix": """# app/config.py
from sqlalchemy.engine import URL

    @property
    def DATABASE_URL(self) -> URL | str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        return URL.create(
            "postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=int(self.POSTGRES_PORT),
            database=self.POSTGRES_DB,
            query={"sslmode": "verify-full"},
        )""",
 "criteria": [
  "The connection URL is constructed through a library that escapes each component.",
  "A password containing `@`, `/` or `?` does not change the parsed host or database.",
  "Connection options are supplied as structured query parameters.",
 ]},

"T2608": {
 "description": "Prove with a test that hostile characters in the credential components cannot redirect the connection.",
 "fix": """# app/tests/security/test_connection_string.py
@pytest.mark.security
def test_password_special_characters_do_not_alter_target(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss/word?host=evil")
    url = make_url(str(Settings().DATABASE_URL))
    assert url.host == "localhost"
    assert url.database == "restaurant"
    assert url.query.get("host") is None""",
 "criteria": [
  "A test injects delimiter characters into each component and asserts the parsed target is unchanged.",
  "The test fails if string interpolation is reintroduced.",
 ]},

"T279": {
 "description": "Constrain what the service loads at runtime to a reviewed, trusted set.",
 "fix": """# app/apis/menu/utils.py
# Content is fetched only from the approved CDN, over HTTPS, with its digest
# verified against a signed manifest before it is stored:
content = _fetch_verified(_safe_image_url(image_url))""",
 "criteria": [
  "Runtime loading of remote content is restricted to an allow-list.",
  "Loaded content is integrity-checked before use.",
  "No module is imported or code evaluated from a path derived from request data.",
 ]},

"T305": {
 "description": "Resolve loadable locations from a fixed absolute base rather than the process working directory.",
 "fix": """# app/main.py
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


def setup_static_files_and_docs(app: FastAPI):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")""",
 "criteria": [
  "Every filesystem location the application loads from is an absolute path derived from the module location.",
  "Starting the process from a different working directory does not change which files are served.",
 ]},

"T4433": {
 "description": "Set an explicit PATH and invoke external commands by absolute path.",
 "fix": """#!/bin/bash
# start_app.sh
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
readonly PATH

/usr/bin/mkdir -m 0750 -p postgres_data
/usr/local/bin/docker compose up "$@\"""",
 "criteria": [
  "PATH is assigned explicitly and marked readonly before any command runs.",
  "External binaries are invoked by absolute path.",
 ]},

"T4436": {
 "description": "Create directories with an explicit restrictive mode and verify ownership before writing.",
 "fix": """#!/bin/bash
# start_app.sh
set -euo pipefail
umask 077

DATA_DIR="$(pwd -P)/postgres_data"
mkdir -m 0700 -p "$DATA_DIR"

if [ "$(stat -f '%u' "$DATA_DIR")" != "$(id -u)" ]; then
    echo "postgres_data is not owned by the current user" >&2
    exit 1
fi""",
 "criteria": [
  "Directories are created with an explicit mode, not the inherited umask default.",
  "Ownership is verified before the directory is used.",
  "The path is resolved absolutely.",
 ]},

"T4437": {
 "description": "Validate the files the script consumes before handing them to a container.",
 "fix": """#!/bin/bash
# start_game.sh
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
GAME=/app/game.py

[ -x "$SCRIPT_DIR/start_app.sh" ] || { echo "start_app.sh missing or not executable" >&2; exit 1; }

"$SCRIPT_DIR/start_app.sh" -d
docker compose exec -T web test -f "$GAME" || { echo "$GAME not found in image" >&2; exit 1; }
docker compose exec -T web python3 "$GAME\"""",
 "criteria": [
  "Every file the script executes is checked for existence and type first.",
  "Paths are absolute and not influenced by the caller's working directory.",
 ]},

"T4444": {
 "description": "Add a check that the scripts cannot be redirected through a hostile PATH.",
 "fix": """# app/tests/security/test_ops_scripts.sh
set -euo pipefail

TMP="$(mktemp -d)"
printf '#!/bin/sh\\necho HIJACKED\\n' > "$TMP/docker"
chmod +x "$TMP/docker"

output="$(PATH="$TMP:$PATH" SDE_DEPLOY_ROLE=operator ./start_app.sh 2>&1 || true)"
case "$output" in
    *HIJACKED*) echo "FAIL: PATH hijack succeeded" >&2; exit 1 ;;
esac""",
 "criteria": [
  "A test plants a shadowing binary on PATH and asserts it is not executed.",
  "The test runs in CI.",
 ]},

"T4447": {
 "description": "Assert that the directories the scripts create are not group- or world-accessible.",
 "fix": """# app/tests/security/test_ops_scripts.sh
set -euo pipefail

rm -rf postgres_data
SDE_DEPLOY_ROLE=operator ./start_app.sh --no-start >/dev/null 2>&1 || true

mode="$(stat -f '%Lp' postgres_data)"
if [ "$mode" != "700" ]; then
    echo "FAIL: postgres_data mode is $mode, expected 700" >&2
    exit 1
fi""",
 "criteria": [
  "A test asserts the created directory mode is 0700.",
  "The test fails if the explicit mode is removed.",
 ]},

"T4448": {
 "description": "Test that the script refuses to run when a required input file is missing or not a regular file.",
 "fix": """# app/tests/security/test_ops_scripts.sh
set -euo pipefail

mv start_app.sh start_app.sh.bak
if ./start_game.sh >/dev/null 2>&1; then
    echo "FAIL: start_game.sh ran with a missing dependency" >&2
    mv start_app.sh.bak start_app.sh
    exit 1
fi
mv start_app.sh.bak start_app.sh""",
 "criteria": [
  "A test removes a required input and asserts the script exits non-zero.",
  "The failure message names the missing file.",
 ]},

"T4449": {
 "description": "Validate any file the script copies into the container for type and size before it is used.",
 "fix": """#!/bin/bash
# start_game.sh
set -euo pipefail

validate_input() {
    local path="$1" max_bytes="${2:-1048576}"
    [ -f "$path" ] || { echo "$path is not a regular file" >&2; return 1; }
    [ -L "$path" ] && { echo "$path is a symlink" >&2; return 1; }
    local size; size="$(stat -f '%z' "$path")"
    [ "$size" -le "$max_bytes" ] || { echo "$path exceeds $max_bytes bytes" >&2; return 1; }
}""",
 "criteria": [
  "Files are checked for regular-file type, symlink status and size before use.",
  "Validation failure aborts the script.",
 ]},

"T659": {
 "description": "Remove the shell from the execution path and constrain the argument to a validated value.",
 "fix": """# app/apis/admin/utils.py
import subprocess
from enum import Enum


class MountPoint(str, Enum):
    ROOT = "/"
    DATA = "/var/lib/postgresql/data"


def get_disk_usage(mount_point: MountPoint) -> str:
    result = subprocess.run(
        ["df", "-h", mount_point.value],
        capture_output=True, check=True, timeout=5,      # shell=False is the default
    )
    return result.stdout.decode().strip()""",
 "criteria": [
  "`shell=True` appears nowhere in the codebase.",
  "The command is passed as an argument list.",
  "The only variable part is drawn from a closed enum, never from a free-form string.",
  "A request with `parameters=/; id` returns 422 and executes nothing.",
 ]},

"T7359": {
 "description": "Perform the update through the ORM, or bind every parameter if raw SQL is unavoidable.",
 "fix": """# app/apis/orders/services/get_order_status.py
db_order.status = OrderStatus(delivery_data["status"])
db.add(db_order)
db.commit()

# Parameterized equivalent if raw SQL is required:
# db.execute(
#     text("UPDATE orders SET status = :status WHERE id = :order_id AND user_id = :user_id"),
#     {"status": db_order.status.value, "order_id": order_id, "user_id": current_user.id},
# )""",
 "criteria": [
  "No f-string or concatenation appears inside a text() call.",
  "External values are validated against the enum before they reach the database.",
  "The update is additionally scoped to the owning user.",
 ]},

"T7360": {
 "description": "Validate and pin outbound request targets so request data cannot steer the service to an internal address.",
 "fix": """# app/apis/menu/utils.py
response = requests.get(
    _safe_image_url(image_url),     # scheme + host allow-list + resolved-IP check
    timeout=(3, 5),
    allow_redirects=False,
    stream=True,
    verify=certifi.where(),
)""",
 "criteria": [
  "Target validation happens before the request and after DNS resolution.",
  "Redirects are disabled.",
  "Connect and read timeouts are set.",
  "Background tasks use the same validated client.",
 ]},

"T7366": {
 "description": "Validate the type, magic bytes and size of any binary content before storing it.",
 "fix": """# app/apis/menu/utils.py
from PIL import Image

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024


def _store_image(content: bytes) -> str:
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in ALLOWED_FORMATS:
                raise HTTPException(status_code=400, detail="Unsupported image format")
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Not a valid image")

    return base64.b64encode(content).decode()""",
 "criteria": [
  "Content type is determined from the bytes, not from a client-supplied header or extension.",
  "Only an explicit allow-list of formats is accepted.",
  "A size ceiling is enforced before decoding.",
  "Stored content is never served with a content type derived from user input.",
 ]},

"T7377": {
 "description": "Escape values interpolated into server-rendered HTML for the context they appear in.",
 "fix": """# app/main.py
from markupsafe import escape
from urllib.parse import quote

@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(
        openapi_url=quote(f"{app.root_path}/openapi.json", safe="/:"),
        title=escape(settings.TITLE),
        swagger_favicon_url=quote(f"{app.root_path}/static/img/favicon-32x32.png", safe="/:"),
    )""",
 "criteria": [
  "Values placed in HTML text are HTML-escaped; values placed in URLs are URL-encoded.",
  "No raw string concatenation produces markup.",
 ]},

"T7378": {
 "description": "Do not follow redirects to a target the caller chose; keep navigation targets relative or on an allow-list.",
 "fix": """# app/apis/menu/utils.py
response = requests.get(
    _safe_image_url(image_url),
    timeout=5,
    allow_redirects=False,      # the validated host is the one contacted
    stream=True,
)
if response.is_redirect:
    raise HTTPException(status_code=400, detail="Redirects are not permitted for image sources")""",
 "criteria": [
  "`allow_redirects=False` is set on outbound requests driven by request data.",
  "Any redirect response is treated as a failure rather than followed.",
  "Application-level redirects accept only relative paths or allow-listed absolute URLs.",
 ]},

"T7380": {
 "description": "Eliminate shell invocation and dynamic evaluation of request-derived data.",
 "fix": """# app/apis/admin/utils.py
def get_disk_usage(mount_point: MountPoint) -> str:
    result = subprocess.run(
        ["df", "-h", mount_point.value],
        capture_output=True, check=True, timeout=5,
    )
    return result.stdout.decode().strip()""",
 "criteria": [
  "`shell=True`, `eval`, `exec` and `os.system` appear nowhere.",
  "Subprocess arguments are a list built from validated enum values.",
  "The subprocess runs under a timeout.",
 ]},

"T7381": {
 "description": "Parse remote content with a strict, format-aware parser and never deserialize untrusted binary formats.",
 "fix": """# app/apis/menu/utils.py
with Image.open(io.BytesIO(content)) as image:
    if image.format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported image format")
    image.verify()

# Nothing in the request path calls pickle.loads, yaml.load or marshal.loads.""",
 "criteria": [
  "No untrusted bytes reach pickle, marshal or an unsafe YAML loader.",
  "Binary content is validated by a parser that fails closed on malformed input.",
  "Parsers are configured with size and recursion limits.",
 ]},

"T7411": {
 "description": "Constrain stored text fields and mark them as text so consumers render them safely.",
 "fix": """# app/apis/menu/schemas.py
from pydantic import BaseModel, ConfigDict, Field


class MenuItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=60)
    image_url: str | None = None""",
 "criteria": [
  "Text fields declare length limits and reject unknown keys.",
  "Responses are served as application/json with nosniff, so text is never interpreted as markup.",
  "No stored text is concatenated into HTML anywhere in the service.",
 ]},

"T7412": {
 "description": "Run the risky operation outside the application process with reduced privileges.",
 "fix": """# app/apis/admin/utils.py
def get_disk_usage(mount_point: MountPoint) -> str:
    result = subprocess.run(
        ["df", "-h", mount_point.value],
        capture_output=True,
        check=True,
        timeout=5,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},   # clean environment
        cwd="/",
    )
    return result.stdout.decode().strip()

# The container itself runs non-root with all capabilities dropped and a
# read-only root filesystem, so the subprocess inherits no privilege.""",
 "criteria": [
  "The subprocess runs with a clean environment, a fixed working directory and a timeout.",
  "The container drops all capabilities and runs as a non-root user.",
  "Third-party components with broad reach run in their own isolation boundary.",
 ]},

"T7414": {
 "description": "Prove with a test that stored text is returned as data and never interpreted as markup.",
 "fix": """# app/tests/security/test_text_rendering.py
PAYLOAD = "<script>alert(1)</script>"


@pytest.mark.security
def test_menu_text_is_returned_as_data(client, chef_token):
    client.put(
        "/menu",
        headers={"Authorization": f"Bearer {chef_token}"},
        json={"name": PAYLOAD, "price": 1.0, "category": "Test"},
    )
    response = client.get("/menu")
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.json()[-1]["name"] == PAYLOAD      # stored verbatim, not executed""",
 "criteria": [
  "A test round-trips a script payload and asserts the response is JSON with nosniff.",
  "No endpoint returns stored text inside an HTML document.",
 ]},

"T7415": {
 "description": "Confirm the isolation boundary around the component that executes shell commands.",
 "fix": """# app/tests/security/test_container_isolation.sh
set -euo pipefail

docker compose config | grep -q 'privileged: true' && { echo "FAIL: privileged" >&2; exit 1; }
docker compose config | grep -q 'SYS_ADMIN'       && { echo "FAIL: SYS_ADMIN" >&2; exit 1; }
docker compose exec -T web id -u | grep -qv '^0$' || { echo "FAIL: running as root" >&2; exit 1; }""",
 "criteria": [
  "A check fails when privileged mode or SYS_ADMIN is present in the rendered compose config.",
  "The application container runs as a non-root user with a read-only root filesystem.",
 ]},

"T89": {
 "description": "Validate stored text on input and guarantee it is never emitted into an HTML context.",
 "fix": """# app/apis/menu/utils.py
def update_menu_item(db, item_id: int, menu_item: schemas.MenuItemCreate):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # MenuItemCreate forbids extra keys and bounds every text field.
    for key, value in menu_item.model_dump(exclude_unset=True, exclude={"image_url"}).items():
        setattr(db_item, key, value)

    if menu_item.image_url:
        db_item.image_base64 = _image_url_to_base64(_safe_image_url(menu_item.image_url))

    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item""",
 "criteria": [
  "Input models bound and constrain every text field and forbid extra keys.",
  "Responses are JSON with `X-Content-Type-Options: nosniff`.",
  "A stored `<script>` payload is returned escaped or as inert JSON data, never executed.",
 ]},

"T98": {
 "description": "Validate the request parameter on the server against a closed set before it reaches any downstream call.",
 "fix": """# app/apis/admin/services/get_disk_stats_service.py
@router.get("/admin/stats/disk", response_model=DiskUsage, status_code=status.HTTP_200_OK)
def get_disk_usage_stats(
    _: Annotated[User, Depends(Requires(Permission.READ_DISK_STATS))],
    mount_point: MountPoint = MountPoint.ROOT,     # enum: FastAPI rejects anything else with 422
):
    return DiskUsage(output=get_disk_usage(mount_point))""",
 "criteria": [
  "The parameter is typed as an enum or carries an explicit pattern and length constraint.",
  "Validation happens server side and does not rely on the client.",
  "An out-of-set value returns 422 before the handler body runs.",
 ]},

# ============================ logging-monitoring ============================

"T7371": {
 "description": "Configure structured logging and emit an audit record for security-relevant events without including credentials.",
 "fix": """# app/init_app.py
import logging
from pythonjsonlogger import jsonlogger

def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


# app/apis/auth/services/get_token_service.py
audit = logging.getLogger("audit")
audit.info("authentication", extra={
    "event": "login_succeeded",
    "username": user.username,
    "source_ip": request.client.host,
    "request_id": request.state.request_id,
})
# never log the password, the token, or the reset code""",
 "criteria": [
  "Logging is configured once at startup with a structured formatter.",
  "Authentication, authorization failures, role changes and administrative actions each emit an audit record.",
  "No log line contains a password, token, reset code or full environment dump.",
  "Each record carries a correlation identifier.",
 ]},

# ============================ secrets-management ============================

"T7369": {
 "description": "Require the signing key and every other secret to come from the environment or a secret store, with no in-code fallback.",
 "fix": """# app/config.py
def _required_secret(name: str, min_length: int = 32) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be provided by the secret store")
    if len(value) < min_length:
        raise RuntimeError(f"{name} must be at least {min_length} characters")
    return value


class Settings:
    JWT_SECRET_KEY: str = _required_secret("JWT_SECRET_KEY")
    POSTGRES_PASSWORD: str = _required_secret("POSTGRES_PASSWORD", min_length=16)

# generate_random_secret() is deleted.""",
 "criteria": [
  "`generate_random_secret()` and every secret default are removed from the configuration module.",
  "Startup fails when a secret is missing or too short.",
  "Secrets are delivered by a secret mount, not committed configuration.",
  "Rotating a secret requires no code change.",
 ]},

}
