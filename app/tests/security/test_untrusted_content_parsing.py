"""T7366 / T7381 / T7412: what the bytes are, and where they are parsed.

A digest says the bytes are the ones the caller meant. It says nothing about
what they contain, and the menu stores the result and serves it back. So the
question these tests cover is whether the application decides what remote
content is by parsing it, or by being told.

The command path is here too, for the same reason: `df` output is trusted
because of how the process is started, not because of what it returns.
"""

import io
import subprocess
from hashlib import sha256

import pytest
import requests
from apis.menu import utils
from config import settings
from fastapi import HTTPException
from PIL import Image

pytestmark = pytest.mark.security

TRUSTED_HOST = "cdn.restaurant.example"
TRUSTED_URL = f"https://{TRUSTED_HOST}/burger.png"


@pytest.fixture
def fetchable(monkeypatch):
    """Everything up to the parser passes, so the parser is the subject."""
    monkeypatch.setattr(settings, "ALLOWED_IMAGE_HOSTS", [TRUSTED_HOST])
    monkeypatch.setattr(settings, "CDN_TOKEN", "")
    monkeypatch.setattr(settings, "CONTENT_SIGNING_PUBLIC_KEY_PEM", "")
    monkeypatch.setattr(
        utils.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )


def _encoded(image_format: str, size=(2, 2)) -> bytes:
    buffer = io.BytesIO()
    mode = "RGB" if image_format != "GIF" else "P"
    Image.new(mode, size, 0 if mode == "P" else (1, 2, 3)).save(
        buffer, format=image_format
    )
    return buffer.getvalue()


def _fetch(content: bytes):
    return utils._image_url_to_base64(TRUSTED_URL, sha256(content).hexdigest())


# --- T7366 / T7381: content is identified by parsing it ----------------


@pytest.mark.parametrize("image_format", ["PNG", "JPEG", "GIF", "WEBP"])
def test_a_supported_image_is_accepted(fetchable, requests_mock, image_format):
    content = _encoded(image_format)
    requests_mock.get(TRUSTED_URL, content=content)

    assert _fetch(content)


@pytest.mark.parametrize(
    "content",
    [
        b"<html><body><script>alert(1)</script></body></html>",
        b"<?php system($_GET['c']); ?>",
        b"#!/bin/sh\nrm -rf /\n",
        b"%PDF-1.4\n%\xc7\xec\x8f\xa2\n",
        b"",
    ],
    ids=["html", "php", "shell", "pdf", "empty"],
)
def test_content_that_is_not_an_image_is_refused(fetchable, requests_mock, content):
    """Stored under image_base64 and served back, the only thing deciding how
    a browser treats this is a content type the service never set."""
    requests_mock.get(TRUSTED_URL, content=content)

    with pytest.raises(HTTPException) as exc:
        _fetch(content)

    assert exc.value.status_code == 400


def test_a_valid_image_in_an_unsupported_format_is_refused(fetchable, requests_mock):
    """The allow-list exists so rarely-exercised decoders never run at all."""
    content = _encoded("BMP")
    requests_mock.get(TRUSTED_URL, content=content)

    with pytest.raises(HTTPException) as exc:
        _fetch(content)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Unsupported image format"


def test_a_truncated_image_is_refused(fetchable, requests_mock):
    """A file that parses as far as its header is what a malformed-input
    attack produces; the header alone must not be enough."""
    content = _encoded("PNG", size=(64, 64))[:40]
    requests_mock.get(TRUSTED_URL, content=content)

    with pytest.raises(HTTPException):
        _fetch(content)


def test_an_image_declaring_enormous_dimensions_is_refused(
    fetchable, requests_mock, monkeypatch
):
    """The byte ceiling does not bound this.

    A few kilobytes of valid PNG can declare dimensions that expand to
    gigabytes of pixels, so a transfer limit passes and the decode exhausts
    the process. Checked by lowering the pixel ceiling rather than by
    actually building a bomb, because constructing one would have to allocate
    it here first.
    """
    monkeypatch.setattr(utils, "MAX_IMAGE_PIXELS", 4)
    content = _encoded("PNG", size=(64, 64))
    requests_mock.get(TRUSTED_URL, content=content)

    with pytest.raises(HTTPException) as exc:
        _fetch(content)

    assert exc.value.status_code == 413


def test_nothing_is_returned_when_the_content_is_refused(fetchable, requests_mock):
    """The caller must not receive partially validated bytes."""
    content = b"<html>not an image</html>"
    requests_mock.get(TRUSTED_URL, content=content)

    with pytest.raises(HTTPException):
        result = _fetch(content)
        assert result is None


def test_the_parser_runs_only_after_the_digest_is_checked(fetchable, requests_mock):
    """Order matters: parsing content whose origin is unverified means the
    decoder is the first thing to see attacker-chosen bytes."""
    content = _encoded("PNG")
    requests_mock.get(TRUSTED_URL, content=content)

    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(TRUSTED_URL, "f" * 64)

    assert exc.value.detail == "Content integrity check failed"


def test_no_unsafe_deserializer_is_reachable_from_a_request():
    """pickle, marshal and yaml.load execute what they read.

    Nothing in this application deserializes binary content today. The test
    exists because adding one is a single import and reads as a convenient
    way to cache an object.
    """
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []
    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text()
        for call in (
            "pickle.load",
            "pickle.loads",
            "marshal.load",
            "marshal.loads",
            "yaml.load(",
            "shelve.open",
            "jsonpickle",
        ):
            if call in source:
                offenders.append(f"{path.relative_to(app_dir)}: {call}")

    assert offenders == [], f"unsafe deserialization reachable: {offenders}"


# --- T1144: no template is rendered from user input --------------------


def test_no_template_is_built_from_a_string_at_runtime():
    """Server-side template injection needs a template assembled at runtime.

    Passing user input as template *data* is safe; putting it into the
    template *source* hands the caller the template language, and from there
    Jinja's object graph reaches the interpreter. This looks for the
    construction, since that is the step that cannot be made safe afterwards.
    """
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []
    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text()
        for call in (
            "Template(",
            "from_string(",
            "render_template_string",
            "Environment(",
        ):
            if call in source:
                offenders.append(f"{path.relative_to(app_dir)}: {call}")

    assert offenders == [], f"template constructed at runtime: {offenders}"


# --- T7380 / T659 / T43 / T7412: the command path ----------------------


def test_no_shell_is_spawned_anywhere_in_the_application():
    """shell=True is the difference between an argument and a command."""
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []
    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text()
        for call in ("shell=True", "os.system(", "os.popen(", "subprocess.getoutput"):
            if call in source:
                offenders.append(f"{path.relative_to(app_dir)}: {call}")

    assert offenders == [], f"a shell is reachable from application code: {offenders}"


def test_no_dynamic_code_execution_on_any_input():
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []
    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text()
        for call in ("eval(", "exec(", "compile(", "__import__("):
            if call in source:
                offenders.append(f"{path.relative_to(app_dir)}: {call}")

    assert offenders == [], f"dynamic code execution present: {offenders}"


@pytest.mark.parametrize(
    "injected",
    [
        "; cat /etc/passwd",
        "&& id",
        "| whoami",
        "$(id)",
        "`id`",
        "/ ; rm -rf /",
        "\n id",
    ],
)
def test_shell_metacharacters_in_the_mount_point_carry_no_meaning(injected, mocker):
    """The argument list is the control, so this asserts on what was passed
    to the process rather than on the output."""
    from apis.admin.utils import get_disk_usage

    run = mocker.patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=b"ok"),
    )

    get_disk_usage(injected)

    argv = run.call_args.args[0]
    assert argv[:2] == ["df", "-h"]
    assert argv[2] == injected, "the value was split, so it was not one argument"
    assert len(argv) == 3
    assert run.call_args.kwargs.get("shell") in (None, False)


def test_the_endpoint_refuses_a_mount_point_outside_the_fixed_set(chef_client):
    """Validation at the boundary, so the handler never sees the value."""
    response = chef_client.get("/admin/stats/disk", params={"mount_point": "/etc"})

    assert response.status_code == 422


def test_the_child_process_does_not_inherit_this_process_environment(mocker):
    """It would otherwise receive the signing key and the database password.

    A child that logs or echoes its environment leaks both, and nothing in
    the parent's code would show it.
    """
    from apis.admin.utils import SAFE_PATH, get_disk_usage

    run = mocker.patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=b"ok"),
    )

    get_disk_usage("/")

    env = run.call_args.kwargs["env"]
    assert env == {"PATH": SAFE_PATH, "LC_ALL": "C"}
    assert all(directory.startswith("/") for directory in SAFE_PATH.split(":"))


def test_the_child_process_is_constrained_and_bounded(mocker):
    """cwd so a relative path cannot reach anything uploaded, a timeout so a
    hung command does not hold the worker, and no stdin so a command that
    decides to prompt fails instead of blocking."""
    from apis.admin.utils import get_disk_usage

    run = mocker.patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=b"ok"),
    )

    get_disk_usage("/")

    kwargs = run.call_args.kwargs
    assert kwargs["cwd"] == "/"
    assert 0 < kwargs["timeout"] <= 30
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["check"] is True


def test_a_command_failure_does_not_reach_the_client(mocker, chef_client):
    """The command string, the path and the traceback are all disclosure."""
    mocker.patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, ["df", "-h", "/"], stderr=b"boom"),
    )

    response = chef_client.get("/admin/stats/disk")

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to read disk statistics"
    assert "df" not in response.text


# --- T122: only https, and only to a named host ------------------------


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "gopher://cdn.restaurant.example/x",
        "ftp://cdn.restaurant.example/x",
        "dict://cdn.restaurant.example/x",
        "data:text/html,<script>alert(1)</script>",
        "http://cdn.restaurant.example/x.png",
        "//cdn.restaurant.example/x.png",
    ],
)
def test_only_https_is_fetched(fetchable, url):
    """Every other scheme either reads a local file or speaks a protocol
    whose handler was never meant to receive a remote URL. http is refused
    too: without TLS there is no certificate to check, so the allow-list
    names a host that nothing verifies.
    """
    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(url, "0" * 64)

    assert exc.value.status_code == 400


def test_a_lookalike_host_is_refused(fetchable):
    """Matched exactly rather than by suffix. `cdn.restaurant.example.evil.com`
    ends with the allowed name and is a different host entirely."""
    for host in (
        "cdn.restaurant.example.evil.com",
        "evilcdn.restaurant.example",
        "cdn.restaurant.example@evil.com",
    ):
        with pytest.raises(HTTPException):
            utils._image_url_to_base64(f"https://{host}/x.png", "0" * 64)


def test_a_redirect_is_not_followed(fetchable, requests_mock, mocker):
    """A redirect is how an allowed host hands the request to one that is
    not, after the URL has already been checked."""
    requests_mock.get(
        TRUSTED_URL, status_code=302, headers={"Location": "http://169.254.169.254/"}
    )
    spy = mocker.spy(requests, "get")

    with pytest.raises(Exception):
        utils._image_url_to_base64(TRUSTED_URL, "0" * 64)

    assert spy.call_args.kwargs["allow_redirects"] is False


# --- T7378 / T1392: a redirect is a change of target -------------------


@pytest.mark.parametrize("status_code", [301, 302, 303, 307, 308])
def test_a_redirect_response_is_refused_rather_than_read(
    fetchable, requests_mock, status_code
):
    """raise_for_status treats 3xx as success.

    With redirects disabled the body of a 302 is usually empty, so without an
    explicit refusal those bytes travel on to the digest check and fail there
    -- reporting an integrity problem for what is actually an attempt to send
    this service somewhere else.
    """
    requests_mock.get(
        TRUSTED_URL,
        status_code=status_code,
        headers={"Location": "http://169.254.169.254/latest/meta-data/"},
        content=b"",
    )

    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(TRUSTED_URL, "0" * 64)

    assert exc.value.status_code == 400
    assert "Redirect" in exc.value.detail


def test_the_redirect_target_is_never_contacted(fetchable, requests_mock, mocker):
    """One request, to the host that was validated."""
    requests_mock.get(
        TRUSTED_URL,
        status_code=302,
        headers={"Location": "https://evil.example.com/x.png"},
        content=b"",
    )
    spy = mocker.spy(requests, "get")

    with pytest.raises(HTTPException):
        utils._image_url_to_base64(TRUSTED_URL, "0" * 64)

    assert spy.call_count == 1
    assert spy.call_args.args[0] == TRUSTED_URL


# --- T7377 / T36: the only HTML this service renders --------------------


def test_the_documentation_title_is_escaped(monkeypatch):
    """The helpers interpolate their arguments into markup without escaping.

    The title is configuration rather than request data, so this is not
    reachable from outside today. It is escaped at the point of use anyway,
    because a value read from the environment is one deployment away from
    carrying a `<` and the escaping then does not depend on anyone
    remembering where the value came from.
    """
    import main
    from config import ENV
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Patched through `main`, not through `config`: the secure-defaults tests
    # reload the config module, which replaces `config.settings` with a new
    # object while `main` keeps its reference to the original. Patching the
    # object `main` actually reads is what makes this independent of test
    # ordering.
    monkeypatch.setattr(main.settings, "ENVIRONMENT", ENV.DEVELOPMENT)
    monkeypatch.setattr(
        main.settings, "TITLE", "</title><script>alert(1)</script><title>x"
    )

    # docs_url=None mirrors init_app: FastAPI's own /docs route would
    # otherwise be matched first and this would test the framework's default.
    app = FastAPI(docs_url=None, redoc_url=None)
    main.setup_static_files_and_docs(app)

    body = TestClient(app).get("/docs").text

    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


def test_no_application_response_is_rendered_as_html():
    """Everything is JSON through a response model, which is why there is
    almost no escaping surface here. This fails if that changes."""
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []

    for path in (app_dir / "apis").rglob("*.py"):
        source = path.read_text()
        for renderer in ("HTMLResponse", "Jinja2Templates", "TemplateResponse"):
            if renderer in source:
                offenders.append(f"{path.relative_to(app_dir)}: {renderer}")

    assert offenders == [], f"HTML rendered from a route: {offenders}"


# --- T279 / T305: what the process loads at runtime ---------------------


def test_no_module_is_loaded_dynamically():
    """The remote-content path stores bytes; nothing turns them into code.

    importlib and __import__ with a computed name are how fetched content
    becomes an imported module, so their absence is the property worth
    holding rather than an argument about whether today's callers are safe.
    """
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []

    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text()
        for loader in ("importlib.import_module", "imp.load_source", "__import__("):
            if loader in source:
                offenders.append(f"{path.relative_to(app_dir)}: {loader}")

    assert offenders == [], f"dynamic module loading: {offenders}"


def test_every_filesystem_location_is_resolved_from_the_module():
    """Starting the process from another directory must not change which
    files are served. `StaticFiles(directory="static")` resolved against the
    working directory, so `cd /` and the mount either vanished or pointed at
    whatever was there instead."""
    import pathlib

    import main

    source = (pathlib.Path(main.__file__)).read_text()

    assert 'StaticFiles(directory="static")' not in source
    assert "StaticFiles(directory=STATIC_DIR)" in source
    assert "Path(__file__).resolve().parent" in source
    assert main.STATIC_DIR.is_absolute()
