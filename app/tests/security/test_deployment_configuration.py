"""Deployment configuration is separated from the repository.

Two different failures are covered. The first is a credential committed in
plain sight, which is the one everyone looks for. The second is quieter and
more likely: an environment-specific default, such as a localhost origin,
that makes production start successfully with development settings. Nothing
errors, nothing is obviously wrong, and the allow-list protecting
authenticated responses is pointing at somebody's laptop.
"""

import pathlib
import re
import subprocess

import pytest

pytestmark = pytest.mark.security

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
COMPOSE = REPO_ROOT / "docker-compose.yml"


def _compose_text() -> str:
    return COMPOSE.read_text(encoding="utf-8")


def test_no_credential_is_committed_in_the_compose_file():
    text = _compose_text()

    # Every environment entry must interpolate, never assign a literal.
    assignments = re.findall(r"^\s+- ([A-Z_]+)=(.*)$", text, re.MULTILINE)

    literals = [
        f"{name}={value}"
        for name, value in assignments
        if not value.startswith("${")
        # Fixed topology inside the compose network, not a credential or an
        # environment-specific value.
        and name not in {"POSTGRES_SERVER", "POSTGRES_PORT", "PGDATA"}
    ]

    assert literals == [], f"literal values committed in compose: {literals}"


def test_secrets_have_no_default_and_fail_loudly():
    text = _compose_text()

    for secret in ("POSTGRES_PASSWORD", "JWT_SECRET_KEY", "OTP_HMAC_KEY"):
        match = re.search(rf"{secret}=\$\{{{secret}(.)", text)
        assert match, f"{secret} is not interpolated from the environment"
        assert match.group(1) == ":", (
            f"{secret} uses a default; a deployment that forgets it would "
            "start with a value nobody chose"
        )
        assert f"{secret}:?" in text


def test_environment_specific_values_are_not_committed():
    """A localhost default in production is a silently wrong allow-list."""
    text = _compose_text()

    for setting in ("ALLOWED_HOSTS", "ALLOWED_ORIGINS"):
        assert f"{setting}=${{{setting}:-" not in text, (
            f"{setting} has a committed default, so an environment that "
            "does not set it inherits development values"
        )


def test_each_environment_has_its_own_configuration_source():
    text = _compose_text()

    assert "env_file:" in text
    assert "DEPLOY_ENV" in text, (
        "there is no per-environment configuration source; every "
        "environment would share whatever is committed here"
    )


def test_env_files_cannot_be_committed():
    """The template is tracked; anything holding real values is not."""

    def ignored(path: str) -> bool:
        return (
            subprocess.run(
                ["git", "check-ignore", "-q", path],
                cwd=REPO_ROOT,
                capture_output=True,
            ).returncode
            == 0
        )

    assert ignored(".env")
    assert ignored("deploy/production.env")
    assert ignored("deploy/local.env")
    assert not ignored("deploy/local.env.example"), (
        "the example template is ignored too, so nobody can see the shape "
        "of the configuration they are expected to supply"
    )


def test_the_example_template_contains_no_values_for_secrets():
    example = REPO_ROOT / "deploy" / "local.env.example"
    assert example.exists()

    for line in example.read_text(encoding="utf-8").splitlines():
        if line.startswith(("JWT_SECRET_KEY", "OTP_HMAC_KEY", "POSTGRES_PASSWORD")):
            assert line.endswith("="), (
                f"the example template carries a value for a secret: {line}"
            )


# --- T3932: no committed environment file or credential literal ----------


def _tracked_files() -> list:
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout.splitlines()


@pytest.mark.security
def test_no_environment_file_is_tracked_by_git():
    """Ignoring a file does not help if it was committed before the rule.

    The .gitignore entry stops a new one; this catches one already in
    history, which is the case that actually leaks.
    """
    committed = [
        path
        for path in _tracked_files()
        if re.fullmatch(r"(.*/)?\.env", path)
        or (path.endswith(".env") and not path.endswith(".env.example"))
    ]

    assert committed == [], f"environment files are committed: {committed}"


@pytest.mark.security
@pytest.mark.parametrize(
    "target", ["docker-compose.yml", "Dockerfile", "deploy/local.env.example"]
)
def test_no_credential_literal_appears_in_deployment_files(target):
    path = REPO_ROOT / target
    assert path.exists(), target

    credential_names = (
        "PASSWORD",
        "SECRET",
        "TOKEN",
        "API_KEY",
        "HMAC_KEY",
    )

    offenders = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip().lstrip("-").strip()
        if stripped.startswith("#"):
            continue
        match = re.match(r"([A-Z0-9_]+)=(.*)$", stripped)
        if not match:
            continue
        name, value = match.groups()
        if not any(marker in name for marker in credential_names):
            continue
        # Empty (a template placeholder) or interpolated is fine; a literal
        # is not.
        if value and not value.startswith("${"):
            offenders.append(f"{target}:{number} {name}")

    assert offenders == [], f"credential literals committed: {offenders}"
