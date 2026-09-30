from html import escape
from pathlib import Path
from urllib.parse import quote

from config import ENV, settings
from db.base import Base
from db.session import engine
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from init import load_initial_data
from init_app import init_app

# Resolved from the module location, never from the process working directory,
# and pointing at a directory that holds public assets only.
STATIC_DIR = Path(__file__).resolve().parent / "static"


def setup_static_files_and_docs(app: FastAPI):
    """Setup static files and custom documentation endpoints with favicon"""
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # The interactive documentation is a development aid. In production the
    # routes are never registered, so they 404 rather than being hidden
    # behind a check that a later edit could drop.
    if settings.ENVIRONMENT is ENV.PRODUCTION:
        return

    # These three routes are the only server-rendered HTML this service
    # produces, and the helpers that build it interpolate their arguments into
    # the markup without escaping. The values are configuration rather than
    # request data, so this is not reachable from outside today -- but a title
    # read from the environment is one deployment away from carrying a `<`,
    # and escaping at the point of use costs nothing and does not depend on
    # remembering where the value came from.
    openapi_url = quote(f"{app.root_path}/openapi.json", safe="/:")
    favicon_url = quote(
        f"{app.root_path}/static/img/favicon-32x32.png", safe="/:"
    )
    title = escape(settings.TITLE)

    @app.get("/", include_in_schema=False)
    def root_docs():
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=title,
            swagger_favicon_url=favicon_url,
        )

    @app.get("/docs", include_in_schema=False)
    def overridden_swagger():
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=title,
            swagger_favicon_url=favicon_url,
        )

    @app.get("/redoc", include_in_schema=False)
    def overridden_redoc():
        return get_redoc_html(
            openapi_url=openapi_url,
            title=title,
            redoc_favicon_url=favicon_url,
        )


def start_application():
    app = init_app()
    if settings.DB_BACKEND == "memory":
        Base.metadata.create_all(bind=engine)

    setup_static_files_and_docs(app)
    load_initial_data()
    return app


app = start_application()
