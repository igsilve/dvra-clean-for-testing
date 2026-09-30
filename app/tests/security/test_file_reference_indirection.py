"""No file is opened using a name the caller supplied.

There is no file-serving feature in this application today, so there is no
indirect reference map to build: adding one would be machinery guarding
nothing, and machinery guarding nothing is machinery nobody maintains. What
these tests do instead is make the absence enforced, so the first handler
that opens a path from a request fails the build rather than shipping.

If a file-serving feature is added, the fix is a server-side map from an
opaque reference to a known path, with the authorization check on the mapped
object — not a sanitizer on the caller's string.
"""

import ast
import pathlib

import pytest

pytestmark = pytest.mark.security

APP_ROOT = pathlib.Path(__file__).resolve().parents[2]

FILE_APIS = {"open", "read_text", "read_bytes", "listdir", "remove", "unlink"}

# Names that hold, or plausibly hold, something the caller sent.
REQUEST_DERIVED = (
    "filename",
    "file_name",
    "filepath",
    "file_path",
    "path",
    "document",
    "doc_id",
    "image_url",
    "user_input",
)


def _python_sources():
    for path in (APP_ROOT / "apis").rglob("*.py"):
        yield path
    for name in ("main.py", "init.py", "init_app.py", "game.py"):
        candidate = APP_ROOT / name
        if candidate.exists():
            yield candidate


def test_no_file_api_is_called_with_a_request_derived_name():
    offenders = []

    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            if name not in FILE_APIS:
                continue

            for argument in node.args:
                rendered = ast.dump(argument)
                if any(hint in rendered for hint in REQUEST_DERIVED):
                    offenders.append(
                        f"{path.relative_to(APP_ROOT)}:{node.lineno} {name}()"
                    )

    assert offenders == [], (
        "a file is being opened from a caller-supplied name; resolve an "
        f"opaque reference through a server-side map instead: {offenders}"
    )


def test_static_assets_are_served_from_one_resolved_directory():
    """The one place files are served has a fixed, resolved root."""
    import main

    assert main.STATIC_DIR.is_absolute(), (
        "the static root is relative, so it follows the process working "
        "directory and a different launch point serves different files"
    )
    assert main.STATIC_DIR == main.STATIC_DIR.resolve()
    assert main.STATIC_DIR.name == "static"


def test_the_static_mount_cannot_be_escaped(anon_client):
    for attempt in (
        "/static/../config.py",
        "/static/..%2fconfig.py",
        "/static/....//config.py",
    ):
        response = anon_client.get(attempt)
        assert response.status_code in (400, 404), attempt
        assert "JWT_SECRET_KEY" not in response.text
