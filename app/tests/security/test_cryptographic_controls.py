"""Which primitives are used, and where they come from.

These cover the choice of algorithm, key length and random source rather
than the protocols built on top of them: the transport and token controls
are exercised in test_controls.py and test_symmetric_key_authentication.py.
"""

import ast
import pathlib
import re
import string
import subprocess

import pytest
from apis.referrals.utils import ALPHABET, CODE_LENGTH, _generate_code

pytestmark = pytest.mark.security

APP_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO_ROOT = APP_ROOT.parent


def _application_sources() -> list:
    return [
        path
        for path in APP_ROOT.rglob("*.py")
        if "tests" not in path.parts and "__pycache__" not in path.parts
    ]


# --- T151, T587: the random source --------------------------------------


def test_referral_codes_come_from_the_cryptographic_source():
    import apis.referrals.utils as module

    source = pathlib.Path(module.__file__).read_text()

    assert "import secrets" in source
    assert not re.search(r"^import random\b", source, re.MULTILINE)
    assert "random.choice" not in source


def test_no_module_that_mints_a_credential_imports_random():
    """`random` is a Mersenne Twister: its state is recoverable from a few
    hundred observed outputs, after which every later value is predictable
    rather than merely hard to guess."""
    offenders = []

    for path in _application_sources():
        tree = ast.parse(path.read_text())
        imports_random = any(
            (isinstance(node, ast.Import) and any(a.name == "random" for a in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module == "random")
            for node in ast.walk(tree)
        )
        if not imports_random:
            continue
        text = path.read_text()
        if any(
            word in text
            for word in ("code", "token", "secret", "key", "password", "id")
        ):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == [], f"predictable randomness near credentials: {offenders}"


def test_the_referral_code_carries_at_least_sixty_four_bits():
    entropy = CODE_LENGTH * (len(ALPHABET).bit_length() - 1)

    # 36 characters is a little over 5 bits each; the exact figure is
    # 13 * log2(36) which is about 67.
    assert len(ALPHABET) == 36
    assert CODE_LENGTH >= 13, f"{CODE_LENGTH} characters is about {entropy} bits"


def test_generated_codes_do_not_repeat():
    codes = {_generate_code() for _ in range(500)}

    assert len(codes) == 500


def test_generated_codes_use_the_whole_alphabet():
    """A generator that silently produced only digits would still pass a
    length check."""
    seen = set("".join(_generate_code() for _ in range(200)))

    assert seen & set(string.ascii_uppercase)
    assert seen & set(string.digits)
    assert not seen - set(ALPHABET)


# --- T445, T60: algorithm and key length --------------------------------


def test_the_signing_key_is_at_least_256_bits():
    from config import MIN_SECRET_LENGTH

    assert MIN_SECRET_LENGTH >= 32


def test_no_weak_hash_is_used_for_a_security_decision():
    """md5 and sha1 are not acceptable for signatures, password storage or
    integrity checks."""
    offenders = []

    for path in _application_sources():
        text = path.read_text()
        for weak in ("md5", "sha1"):
            if weak in text.lower():
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {weak}")

    assert offenders == [], f"weak hash referenced: {offenders}"


def test_password_storage_uses_a_deliberate_password_hash():
    """A general-purpose hash is fast, which is the wrong property here."""
    from apis.auth.utils.utils import pwd_context

    schemes = pwd_context.schemes()

    assert schemes
    for scheme in schemes:
        assert scheme.startswith(("argon2", "bcrypt")), scheme


# --- T59, T446: where the primitives come from --------------------------


def test_no_cryptographic_primitive_is_hand_rolled():
    """The failure mode is a home-made construction that looks right, so
    this checks for the shapes of one rather than for a library name."""
    suspicious = (
        re.compile(r"\bdef\s+\w*(encrypt|decrypt|hash_password)\w*\s*\("),
        re.compile(r"\^\s*ord\("),  # xor "cipher"
        re.compile(r"\bbase64\b.*\bpassword\b"),
    )

    offenders = []
    for path in _application_sources():
        text = path.read_text()
        for pattern in suspicious:
            if pattern.search(text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {pattern.pattern}")

    assert offenders == [], f"possible hand-rolled cryptography: {offenders}"


def test_keyed_hashing_uses_a_constant_time_comparison():
    """`==` on a digest leaks how much of it matched, one byte at a time."""
    from apis.auth.utils import text_code_utils

    source = pathlib.Path(text_code_utils.__file__).read_text()

    assert "compare_digest" in source
    assert not re.search(r"reset_password_code\s*==", source)


# --- T156, T175: certificate validation ---------------------------------


def test_certificate_verification_is_never_disabled():
    for path in _application_sources():
        text = path.read_text()

        assert "verify=False" not in text, path
        assert "verify = False" not in text, path
        assert "CERT_NONE" not in text, path
        assert "InsecureRequestWarning" not in text, path


def test_the_trust_store_is_pinned_rather_than_inherited():
    """Inheriting the system store means a certificate added to the host,
    by anything, silently widens who this service will trust."""
    from apis.menu import utils

    source = pathlib.Path(utils.__file__).read_text()

    assert "certifi.where()" in source
    assert "verify=certifi.where()" in source


def test_every_outbound_call_pins_the_bundle_and_refuses_redirects():
    """A redirect is how an allow-listed host hands the request to one that
    is not, after the URL has already been checked."""
    offenders = []

    for path in _application_sources():
        text = path.read_text()
        for match in re.finditer(r"requests\.(get|post|put|delete)\(", text):
            window = text[match.start() : match.start() + 600]
            if "verify=" not in window:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: no verify=")
            if "allow_redirects=False" not in window:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: redirects allowed")
            if "timeout=" not in window:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: no timeout")

    assert offenders == [], offenders


def test_a_certificate_failure_is_not_swallowed(monkeypatch):
    """An SSLError must reach the caller rather than being turned into an
    empty result that the application treats as a successful fetch."""
    import requests
    from apis.menu import utils
    from config import settings

    monkeypatch.setattr(
        settings, "ALLOWED_IMAGE_HOSTS", ["cdn.restaurant.example"]
    )
    # The allow-listed name does not exist, so the resolved-address check
    # (T7360) would refuse it before this test reaches its subject.
    monkeypatch.setattr(
        utils.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )

    def _raise(*args, **kwargs):
        raise requests.exceptions.SSLError("certificate verify failed")

    monkeypatch.setattr(requests, "get", _raise)

    with pytest.raises(requests.exceptions.SSLError):
        utils._image_url_to_base64(
            "https://cdn.restaurant.example/x.png", "0" * 64
        )


# --- T4443, T4454: the shell tooling ------------------------------------


def _shell_scripts() -> list:
    listed = subprocess.run(
        ["git", "ls-files", "*.sh"], cwd=REPO_ROOT, capture_output=True, text=True
    )
    return [REPO_ROOT / name for name in listed.stdout.split()]


def test_shell_scripts_exist_to_check():
    assert _shell_scripts()


def test_no_shell_script_contains_a_credential_literal():
    offenders = []

    for path in _shell_scripts():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            match = re.search(
                r"\b([A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY))=(\S*)", stripped
            )
            if match and match.group(3) and not match.group(3).startswith(("$", '"$')):
                offenders.append(f"{path.name}:{number}")

    assert offenders == [], f"credential literals in shell scripts: {offenders}"


def test_no_shell_script_echoes_a_credential():
    """Anything echoed lands in a terminal scrollback, a CI log, or both."""
    offenders = []

    for path in _shell_scripts():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if re.search(r"\b(echo|printf)\b", line) and re.search(
                r"PASSWORD|SECRET|TOKEN|_KEY", line
            ):
                offenders.append(f"{path.name}:{number}")

    assert offenders == [], offenders


@pytest.mark.parametrize("script", ["start_app.sh", "stop_app.sh"])
def test_scripts_restrict_the_mode_of_anything_they_create(script):
    text = (REPO_ROOT / script).read_text()
    lines = [line.strip() for line in text.splitlines()]

    assert "umask 077" in lines, f"{script} sets no umask"

    # Before the first thing it creates, not after.
    umask_at = lines.index("umask 077")
    for index, line in enumerate(lines):
        if line.startswith(("mkdir", "touch", "tee", "cat >")):
            assert index > umask_at, f"{script} creates {line!r} before the umask"


@pytest.mark.parametrize("script", ["start_app.sh", "stop_app.sh"])
def test_scripts_do_not_export_secrets_into_the_container(script):
    """Secrets reach the runtime from the environment file the platform
    supplies, so a script that exported one would be a second, unreviewed
    path for the same value."""
    text = (REPO_ROOT / script).read_text()

    assert not re.search(r"export\s+[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|KEY)", text)
