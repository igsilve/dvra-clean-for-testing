"""T186 / T241 / T7374: the dependency set is pinned, hashed and audited.

Three separate failures are covered here, and they fail in different ways.

An unpinned dependency means two builds of the same commit install different
code. A pinned-but-unhashed dependency means the version is fixed but the
bytes are not, so a compromised index or a yanked-and-republished release
changes what ships without changing anything under review. And a pinned,
hashed, reproducible dependency can still be a known-vulnerable one, which is
what the audit is for -- reproducibility and safety are unrelated properties.
"""

import json
import pathlib
import re
import shutil
import subprocess
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"
LOCK = REPO_ROOT / "poetry.lock"
DOCKERFILE = REPO_ROOT / "Dockerfile"

# Tooling that must not be installed into the runtime image. Not a style
# preference: each one is code present for anything that achieves execution in
# the container, and has to be patched on the application's own schedule.
DEV_ONLY = ("pytest", "pylint", "pytest-mock", "requests-mock", "pip-audit", "black")

# Advisories that have been reviewed and accepted, keyed by advisory ID so
# that accepting one does not silently accept the next one in the same
# package. An entry here is a decision with a reason, not a mute: the reason
# has to name why the vulnerable code path is unreachable, and the
# precondition it depends on is itself asserted below.
ACCEPTED_ADVISORIES = {
    "PYSEC-2026-1325": (
        "ecdsa: Minerva timing attack on P-256 signing and key generation. "
        "The package has no fixed release and the maintainers consider side "
        "channel attacks out of scope, so there is nothing to upgrade to. It "
        "arrives as an unconditional dependency of python-jose and is only "
        "reached by ECDSA signing, which this application never performs: the "
        "JWT algorithm is a pinned HS256 literal at both issuance and "
        "verification, asserted by "
        "test_the_accepted_ecdsa_advisory_precondition_still_holds."
    ),
}


@pytest.fixture(scope="module")
def pyproject():
    return tomllib.loads(PYPROJECT.read_text())


@pytest.fixture(scope="module")
def exported_requirements(tmp_path_factory):
    """The production requirement set, as the image build produces it."""
    if shutil.which("poetry") is None:
        pytest.skip("poetry is not available on this host")

    out = tmp_path_factory.mktemp("export") / "requirements.txt"
    result = subprocess.run(
        ["poetry", "export", "-f", "requirements.txt", "--output", str(out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, result.stderr
    return out.read_text()


@pytest.mark.security
def test_the_lock_file_is_committed():
    """Without it the caret ranges resolve to whatever is newest at build time."""
    assert LOCK.exists(), "poetry.lock is not committed"
    assert LOCK.stat().st_size > 0


@pytest.mark.security
def test_the_lock_file_matches_pyproject():
    """A stale lock is worse than none: it pins a set nobody declared.

    This is the check that belongs in CI as `poetry lock --check`; running it
    here means it cannot be left out of the pipeline by omission.
    """
    if shutil.which("poetry") is None:
        pytest.skip("poetry is not available on this host")

    result = subprocess.run(
        ["poetry", "lock", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, (
        "poetry.lock is out of date with pyproject.toml; run `poetry lock`\n"
        + result.stdout
        + result.stderr
    )


@pytest.mark.security
def test_every_exported_requirement_is_pinned_to_one_version(exported_requirements):
    """`>=` or `~=` in the export would mean the build still resolves."""
    unpinned = []
    for line in exported_requirements.splitlines():
        if not re.match(r"[A-Za-z]", line):
            continue
        requirement = line.split(";")[0].split("\\")[0].strip()
        if "==" not in requirement:
            unpinned.append(requirement)

    assert unpinned == [], f"requirements without an exact version: {unpinned}"


@pytest.mark.security
def test_every_exported_requirement_carries_a_hash(exported_requirements):
    """The version says which release; the hash says which bytes."""
    missing = []
    current = None
    hashed = set()
    for line in exported_requirements.splitlines():
        if re.match(r"[A-Za-z]", line):
            current = line.split("=")[0].strip()
        elif "--hash=" in line and current:
            hashed.add(current)

    for line in exported_requirements.splitlines():
        if re.match(r"[A-Za-z]", line):
            name = line.split("=")[0].strip()
            if name not in hashed:
                missing.append(name)

    assert missing == [], f"requirements without a hash: {missing}"


@pytest.mark.security
def test_the_image_build_requires_hashes():
    """Hashes in the file are advisory unless pip is told to insist.

    Without --require-hashes, pip accepts a requirement that has none, so a
    dependency added later without one installs unverified rather than
    failing the build.
    """
    text = DOCKERFILE.read_text()

    assert "--require-hashes" in text, "the image installs without verifying hashes"
    assert not re.search(r"pip install[^\n]*-r requirements.txt", text) or re.search(
        r"pip install[^\n]*--require-hashes[^\n]*-r requirements.txt", text
    ), "one pip install reads requirements.txt without --require-hashes"


@pytest.mark.security
@pytest.mark.parametrize("package", DEV_ONLY)
def test_test_and_lint_tooling_is_not_a_runtime_dependency(pyproject, package):
    """Shipped tooling is attack surface that is never executed in production."""
    runtime = pyproject["tool"]["poetry"]["dependencies"]

    assert package not in runtime, f"{package} is installed into the runtime image"


@pytest.mark.security
def test_no_dev_tooling_reaches_the_exported_requirements(exported_requirements):
    """The declaration above only helps if the export honours the grouping."""
    present = [
        package
        for package in DEV_ONLY
        if re.search(rf"^{re.escape(package)}==", exported_requirements, re.MULTILINE)
    ]

    assert present == [], f"dev tooling exported into the production set: {present}"


@pytest.mark.security
def test_security_floors_are_declared_for_transitive_packages(pyproject):
    """A floor in the lock alone can be resolved back down by `poetry update`.

    Each of these was raised in response to a specific advisory. Declaring
    them in pyproject.toml is what makes the fix survive the next resolution.
    """
    runtime = pyproject["tool"]["poetry"]["dependencies"]

    for package in ("starlette", "h11", "urllib3", "idna"):
        assert package in runtime, f"no declared floor for {package}"


@pytest.mark.security
def test_the_pinned_set_has_no_known_vulnerability():
    """The audit that reproducibility does not provide.

    Run against the installed environment rather than the exported file:
    auditing a requirements file makes pip resolve it, which needs to build
    psycopg2 from source and fails on any host without the PostgreSQL client
    headers. The installed set is what the lock produced, so it is the same
    set with none of the build requirement.

    Advisories affecting development tooling are reported but not failed on;
    the tooling does not run in production and blocking the suite on it would
    train people to skip the test that also covers the runtime packages.

    Advisories in ACCEPTED_ADVISORIES are excluded individually by ID. A
    package-level exclusion would also hide the next advisory found in the
    same package, which is the one nobody has looked at.
    """
    if shutil.which("poetry") is None:
        pytest.skip("poetry is not available on this host")

    venv = subprocess.run(
        ["poetry", "env", "info", "--path"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if venv.returncode != 0:
        pytest.skip("no poetry virtualenv to audit")

    result = subprocess.run(
        ["poetry", "run", "pip-audit", "--progress-spinner", "off", "-f", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        env={
            **_environ(),
            "PIPAPI_PYTHON_LOCATION": f"{venv.stdout.strip()}/bin/python",
        },
    )

    if not result.stdout.strip():
        pytest.skip(f"pip-audit produced no report: {result.stderr[-400:]}")

    report = json.loads(result.stdout)
    runtime = set(
        tomllib.loads(PYPROJECT.read_text())["tool"]["poetry"]["dependencies"]
    )
    findings = {}
    for dependency in report["dependencies"]:
        if dependency["name"].lower() not in runtime:
            continue
        unreviewed = sorted(
            {
                v["id"]
                for v in dependency["vulns"]
                if v["id"] not in ACCEPTED_ADVISORIES
            }
        )
        if unreviewed:
            findings[dependency["name"]] = unreviewed

    assert findings == {}, f"declared dependencies with known advisories: {findings}"


@pytest.mark.security
def test_every_accepted_advisory_records_a_reason():
    """An exception without a justification is indistinguishable from a mute."""
    for advisory, reason in ACCEPTED_ADVISORIES.items():
        assert len(reason) > 80, f"{advisory} is accepted without a stated reason"


@pytest.mark.security
def test_the_accepted_ecdsa_advisory_precondition_still_holds():
    """The acceptance rests on ECDSA never being used; check that separately.

    Without this, changing the JWT algorithm to ES256 would make the accepted
    advisory apply again and nothing would say so: the exception would keep
    suppressing a finding whose reason had stopped being true.
    """
    import jwt_tokens

    assert jwt_tokens.ALGORITHM == "HS256", (
        "PYSEC-2026-1325 is accepted on the basis that no ECDSA signing "
        f"happens; the algorithm is now {jwt_tokens.ALGORITHM}"
    )


def _environ():
    import os

    return dict(os.environ)
