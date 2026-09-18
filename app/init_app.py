from apis.router import api_router
from config import settings
import logging
import secrets
import time
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from rate_limiting import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


logger = logging.getLogger("security.audit")


def init_app():
    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        servers=settings.SERVERS,
        root_path=settings.ROOT_PATH,
        docs_url=None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https://([a-zA-Z0-9-]+\.)?(restaurant\.com|deliveryservice\.com)$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    )

    @app.middleware("http")
    async def add_clickjacking_headers(request: Request, call_next):
        start_time = time.perf_counter()
        state_changing_methods = {"POST", "PUT", "PATCH", "DELETE"}
        exempt_paths = {"/token", "/register", "/healthcheck"}
        has_cookie = bool(request.headers.get("cookie"))

        if (
            request.method in state_changing_methods
            and has_cookie
            and request.url.path not in exempt_paths
        ):
            csrf_cookie = request.cookies.get("csrf_token")
            csrf_header = request.headers.get("X-CSRF-Token")
            if not csrf_cookie or not csrf_header:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Missing CSRF token"},
                )
            if not secrets.compare_digest(csrf_cookie, csrf_header):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid CSRF token"},
                )

        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        if not request.cookies.get("csrf_token"):
            response.set_cookie(
                key="csrf_token",
                value=secrets.token_urlsafe(32),
                httponly=False,
                secure=True,
                samesite="lax",
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            "request_audit method=%s path=%s status=%s client=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            client_host,
            duration_ms,
        )
        return response

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(api_router)

    return app
