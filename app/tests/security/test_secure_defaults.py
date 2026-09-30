"""CT9 / T2349 / T2357: nothing security-relevant has a default.

The failure these cover is not a weak value chosen by mistake. It is that an
incomplete environment used to produce a process that started, logged nothing
unusual and passed a health check, while signing tokens with a generated key
and connecting to the database as "admin"/"password". A deployment that is
missing its configuration should be an obvious outage, not a quiet weakness.

Each test reloads `config` with one variable removed, which is the only way to
observe an import-time check. Reloading leaves the module in whatever state
the last successful import produced, so the fixture restores it afterwards --
otherwise a failure here would cascade into every later test in the session.
"""

import ast
import importlib
import os
import pathlib

import pytest

import config

REQUIRED_SETTINGS = (
    "JWT_SECRET_KEY",
    "OTP_HMAC_KEY",
    "CHEF_USERNAME",
    "ENV",
)

# Values that used to be defaults. Asserted as absent by value, because
# re-adding one as a default is a one-line change that reads as a convenience.
FORMER_DEFAULTS = {
    "CHEF_USERNAME": "chef",
    "POSTGRES_USER": "admin",
    "POSTGRES_PASSWORD": "password",
}


@pytest.fixture
def restored_config():
    """Reload the real configuration after a test has broken it."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)
    importlib.reload(config)


@pytest.mark.security
@pytest.mark.parametrize("name", REQUIRED_SETTINGS)
def test_startup_fails_without_a_required_setting(monkeypatch, restored_config, name):
    monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError) as raised:
        importlib.reload(config)

    assert name in str(raised.value)


@pytest.mark.security
@pytest.mark.parametrize("name", ("JWT_SECRET_KEY", "OTP_HMAC_KEY"))
def test_the_failure_does_not_disclose_the_value(monkeypatch, restored_config, name):
    """A configuration error must not print the secret it was reading.

    Only the secrets: the ENV error deliberately quotes the value it was
    given, because "ENV=prod is not recognised" is the message that tells an
    operator what they mistyped, and the environment name is not a secret.
    """
    monkeypatch.setenv(name, "too-short")

    with pytest.raises(RuntimeError) as raised:
        importlib.reload(config)

    assert "too-short" not in str(raised.value)


@pytest.mark.security
def test_the_environment_has_no_default(monkeypatch, restored_config):
    """Neither direction is safe, so there is no default at all.

    Defaulting to production gave a process that called itself production and
    was configured like a laptop. Defaulting to development would silently
    enable debug behaviour in a real deployment.
    """
    monkeypatch.delenv("ENV", raising=False)

    with pytest.raises(RuntimeError) as raised:
        importlib.reload(config)

    assert "ENV" in str(raised.value)


@pytest.mark.security
def test_an_unrecognised_environment_is_refused(monkeypatch, restored_config):
    """A typo must not fall through to a permissive setting."""
    monkeypatch.setenv("ENV", "prod")

    with pytest.raises(RuntimeError) as raised:
        importlib.reload(config)

    assert "production" in str(raised.value), "the error does not say what is valid"


@pytest.mark.security
def test_no_former_default_is_reachable_from_the_source():
    """The old values must not come back as a convenience default."""
    source = pathlib.Path(config.__file__).read_text()

    for name, value in FORMER_DEFAULTS.items():
        assert f'os.getenv("{name}", "{value}")' not in source, (
            f"{name} has been given back its old default of {value!r}"
        )


@pytest.mark.security
@pytest.mark.parametrize(
    "name", ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_SERVER", "POSTGRES_DB")
)
def test_the_database_credentials_are_required_when_a_database_is_used(
    monkeypatch, restored_config, name
):
    """Under DB_BACKEND=memory there is no connection, so no credential.

    The suite runs on the in-memory backend, which means the Postgres
    requirement is not exercised by any other test. This one switches the
    backend so the check is actually observed rather than assumed.

    The others are supplied so the missing one is the reason for the failure;
    otherwise this would only ever prove that whichever setting is read first
    is required.
    """
    monkeypatch.setenv("DB_BACKEND", "postgres")
    for supplied in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_SERVER", "POSTGRES_DB"):
        monkeypatch.setenv(supplied, "supplied-by-the-test")
    monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError) as raised:
        importlib.reload(config)

    assert name in str(raised.value)


@pytest.mark.security
def test_signature_verification_is_not_configurable():
    """The finding included a JWT_VERIFY_SIGNATURE switch read from the environment."""
    source = pathlib.Path(config.__file__).read_text()

    assert 'os.getenv("JWT_VERIFY_SIGNATURE"' not in source


# --- T7369 / T76 / T1186 / T1187: where secrets are not -----------------


@pytest.mark.security
def test_the_random_secret_generator_is_gone():
    """generate_random_secret() returned six digits from a fixed alphabet
    and was the default for JWT_SECRET_KEY. Every replica generated its own,
    so tokens were both guessable and not interchangeable between them."""
    source = (pathlib.Path(__file__).resolve().parents[2] / "config.py").read_text()

    assert "generate_random_secret" not in source
    assert "random.choices" not in source


@pytest.mark.security
def test_no_configuration_value_defaults_to_a_secret():
    """Every os.getenv in the configuration module either has no default or
    has one that is not a credential. A default secret is the version that
    ships when the deployment forgets to set it."""
    source = (pathlib.Path(__file__).resolve().parents[2] / "config.py").read_text()
    tree = ast.parse(source)
    offenders = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "getenv"):
            continue
        if len(node.args) < 2:
            continue
        # An empty-string default is the absence of a value, not a
        # credential: the optional integrations below are off unless the
        # deployment supplies a token, and "" is how they say so.
        default = node.args[1]
        if isinstance(default, ast.Constant) and default.value == "":
            continue
        name = node.args[0].value if isinstance(node.args[0], ast.Constant) else ""
        if any(
            marker in str(name).lower()
            for marker in ("secret", "password", "key", "token", "hmac")
        ):
            offenders.append(name)

    assert offenders == [], f"secret with a default: {offenders}"


@pytest.mark.security
def test_no_source_file_contains_a_hardcoded_credential():
    """The broad sweep for T76. Assignments of a literal to a
    credential-shaped name, found by AST so that prose in a comment or a
    docstring explaining the fix does not trip it."""
    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []

    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text())

        # Enum members are names, not values: Permission.RESET_CHEF_PASSWORD
        # = "manage:chef_password" is an identifier for a permission, and
        # flagging it would mean either renaming the permission or muting
        # the check.
        enum_bodies = {
            id(child)
            for cls in ast.walk(tree)
            if isinstance(cls, ast.ClassDef)
            and any(
                "Enum" in ast.unparse(base) or "enum" in ast.unparse(base)
                for base in cls.bases
            )
            for child in cls.body
        }

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            if id(node) in enum_bodies:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if not any(
                marker in n.lower()
                for n in names
                for marker in ("password", "secret", "hmac_key", "api_key")
            ):
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if value.value:
                    offenders.append(
                        f"{path.relative_to(app_dir)}:{node.lineno} {names}"
                    )

    assert offenders == [], f"hardcoded credential: {offenders}"


@pytest.mark.security
def test_the_dockerfile_carries_no_secret():
    """T1186. ENV and ARG values persist in the image's layer history, so a
    secret placed there is readable by anyone who can pull the image --
    including after the line is deleted in a later layer."""
    dockerfile = (
        pathlib.Path(__file__).resolve().parents[3] / "Dockerfile"
    ).read_text()
    offenders = []

    for line in dockerfile.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        directive = stripped.split(None, 1)[0].upper()
        if directive not in ("ENV", "ARG", "RUN", "LABEL"):
            continue
        for marker in (
            "PASSWORD",
            "SECRET",
            "TOKEN",
            "API_KEY",
            "PRIVATE_KEY",
            "HMAC",
        ):
            if marker in stripped.upper():
                offenders.append(stripped)

    assert offenders == [], f"secret in the Dockerfile: {offenders}"


@pytest.mark.security
def test_no_secret_is_copied_into_the_image():
    """T1187. An .env file copied in is the same disclosure as an ENV line,
    with the added problem that it is easy to miss in a broad COPY."""
    dockerfile = (
        pathlib.Path(__file__).resolve().parents[3] / "Dockerfile"
    ).read_text()

    for line in dockerfile.splitlines():
        stripped = line.strip()
        if not stripped.upper().startswith("COPY"):
            continue
        assert ".env" not in stripped, f"copies an env file: {stripped}"
        assert not stripped.split()[1:2] == ["."], (
            f"copies the whole build context, which would include any local "
            f"secret file: {stripped}"
        )


@pytest.mark.security
def test_local_secret_files_are_excluded_from_the_build_context():
    """T214, to the extent source control can carry it: the host-side file
    permissions belong to the platform, but keeping the files out of the
    image and out of git is the part this repository controls."""
    root = pathlib.Path(__file__).resolve().parents[3]

    dockerignore = (root / ".dockerignore").read_text()
    assert ".env" in dockerignore

    gitignore = (root / ".gitignore").read_text()
    assert ".env" in gitignore
