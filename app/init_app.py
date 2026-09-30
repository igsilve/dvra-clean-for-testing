import secrets

from apis.router import api_router
from audit_log import audit, configure_logging
from config import ENV, settings
from error_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rate_limiting import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
        response.headers["Cache-Control"] = "no-store"
        # Starlette's MutableHeaders has no pop(); use del, which is a no-op
        # guard away from raising KeyError when the header is absent.
        for leaky in ("X-Powered-By", "Server"):
            if leaky in response.headers:
                del response.headers[leaky]
        return response


class CsrfMiddleware(BaseHTTPMiddleware):
    """Require a non-ambient credential on unsafe requests.

    Authentication is Bearer-token only today, so the browser never attaches
    credentials cross-site and this check has nothing to do. It is installed
    anyway so that introducing cookie authentication later fails closed: the
    moment a request carries an auth cookie, an unsafe method without a
    matching double-submit token is rejected.
    """

    SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
    AUTH_COOKIES = ("access_token", "session", "session_id")

    async def dispatch(self, request, call_next):
        if request.method not in self.SAFE_METHODS and any(
            name in request.cookies for name in self.AUTH_COOKIES
        ):
            header = request.headers.get("X-CSRF-Token")
            cookie = request.cookies.get("csrf_token")
            # compare_digest, not ==, so a mismatch cannot be found by timing.
            if (
                not header
                or not cookie
                or not secrets.compare_digest(header, cookie)
            ):
                return JSONResponse(
                    {"detail": "CSRF token missing or invalid"}, status_code=403
                )

        return await call_next(request)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized bodies before they are buffered into memory."""

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request, call_next):
        declared = request.headers.get("content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_bytes:
                    return JSONResponse(
                        {"detail": "Request body too large"}, status_code=413
                    )
            except ValueError:
                return JSONResponse(
                    {"detail": "Invalid Content-Length"}, status_code=400
                )

        if request.headers.get("transfer-encoding", "").lower() == "chunked":
            received = 0
            chunks = []
            async for chunk in request.stream():
                received += len(chunk)
                if received > self.max_bytes:
                    return JSONResponse(
                        {"detail": "Request body too large"}, status_code=413
                    )
                chunks.append(chunk)
            body = b"".join(chunks)

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive

        return await call_next(request)


class AccessAuditMiddleware(BaseHTTPMiddleware):
    """Record the security-relevant outcome of requests.

    Not every request: an audit trail that logs each menu read is one nobody
    reads. What is recorded is every refusal (401, 403, 429), every server
    error, and every state-changing method whatever its outcome -- the three
    categories an incident review actually asks about.

    `request.url.path` and not the full URL: the query string is where a
    reset code or a token ends up when a client puts one there, and it would
    otherwise be copied into the log verbatim.
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        changes_state = request.method in ("POST", "PUT", "PATCH", "DELETE")
        refused = response.status_code in (401, 403, 429)

        if changes_state or refused or response.status_code >= 500:
            audit(
                "http_request",
                outcome="denied" if refused else (
                    "error" if response.status_code >= 400 else "success"
                ),
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client_ip=request.client.host if request.client else None,
            )

        return response


def init_app():
    # Before the app object exists, so that a failure during startup is
    # itself recorded in the structured format rather than in whatever
    # logging.basicConfig would have improvised on first use.
    configure_logging()

    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        servers=settings.SERVERS,
        root_path=settings.ROOT_PATH,
        docs_url=None,
        redoc_url=None,
        # The schema is what makes the interactive docs useful, so it is
        # withdrawn in production alongside them. Leaving it served would
        # publish every route, parameter and model shape to anonymous callers.
        openapi_url=(
            None if settings.ENVIRONMENT is ENV.PRODUCTION else "/openapi.json"
        ),
    )
    # Starlette makes the LAST-registered middleware the outermost layer, so
    # these are added innermost-first. SecurityHeadersMiddleware must be
    # registered last: the layers below it short-circuit with their own
    # responses (TrustedHost 400, BodySizeLimit 413/400), and those replies
    # only carry the security headers if they pass back out through it.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    if settings.ENVIRONMENT is ENV.PRODUCTION:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.MAX_BODY_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )
    app.add_middleware(CsrfMiddleware)
    # Registered after CSRF and before the header layer, so a request the
    # CSRF check refuses is still recorded.
    app.add_middleware(AccessAuditMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Error bodies are shaped explicitly so they cannot echo submitted input.
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(api_router)

    return app
