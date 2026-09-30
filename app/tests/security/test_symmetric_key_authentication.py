"""The symmetric signing key must come from outside the application.

A generated fallback is worse than no key handling at all: the process
starts, signs tokens, serves traffic and reports healthy, while the thing
protecting every identity in the system is whatever the application made up
on boot. The previous fallback was six decimal digits. These tests pin both
halves — the key is supplied and long enough (T406), and the signature it
produces is actually checked (T407).
"""

import base64
import inspect
import json
import os
import subprocess
import sys

import pytest
from config import MIN_SECRET_LENGTH, settings
from jose import jwt

pytestmark = pytest.mark.security

REQUIRED_SECRETS = ["JWT_SECRET_KEY", "OTP_HMAC_KEY"]


def _b64(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _import_config_with(env: dict) -> subprocess.CompletedProcess:
    """Import the configuration in a fresh process under a given environment.

    A subprocess rather than monkeypatching, because the failure being
    tested happens at import time and the module is already imported here.
    """
    child_env = {
        key: value
        for key, value in os.environ.items()
        if key not in REQUIRED_SECRETS
    }
    child_env.update(env)

    return subprocess.run(
        [sys.executable, "-c", "import config"],
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        env=child_env,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("missing", REQUIRED_SECRETS)
def test_the_process_refuses_to_start_without_a_supplied_key(missing):
    supplied = {
        name: "x" * MIN_SECRET_LENGTH
        for name in REQUIRED_SECRETS
        if name != missing
    }

    result = _import_config_with(supplied)

    assert result.returncode != 0, (
        f"the application started with no {missing}, which means it "
        "invented one and is signing with a value nobody chose"
    )
    assert missing in result.stderr


@pytest.mark.parametrize("name", REQUIRED_SECRETS)
def test_a_short_key_is_rejected(name):
    supplied = {other: "x" * MIN_SECRET_LENGTH for other in REQUIRED_SECRETS}
    supplied[name] = "x" * (MIN_SECRET_LENGTH - 1)

    result = _import_config_with(supplied)

    assert result.returncode != 0, f"{name} was accepted below the minimum length"


def test_the_failure_does_not_echo_the_key():
    """A startup error lands in logs that are less protected than the key."""
    secret = "sup3r-secret-value-that-must-not-appear" + "x" * MIN_SECRET_LENGTH
    supplied = {"JWT_SECRET_KEY": secret, "OTP_HMAC_KEY": "short"}

    result = _import_config_with(supplied)

    assert result.returncode != 0
    assert secret not in result.stderr
    assert secret not in result.stdout


def test_no_key_material_is_generated_inside_the_application():
    import config

    source = inspect.getsource(config)

    assert "generate_random_secret" not in source, (
        "the configuration module still generates key material, so a "
        "deployment that forgets to supply a key silently gets one"
    )
    assert "random.choices" not in source


def test_an_unsigned_token_is_rejected(anon_client):
    """alg=none asks the verifier to take the claims on trust.

    Asserted by behaviour rather than by grepping for the string 'none',
    which matches the comments explaining why it is refused.
    """
    header = _b64({"alg": "none", "typ": "JWT"})
    payload = _b64(
        {
            "sub": "chef",
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }
    )
    unsigned = f"{header}.{payload}."

    response = anon_client.get(
        "/admin/stats/disk", headers={"Authorization": f"Bearer {unsigned}"}
    )

    assert response.status_code == 401


def test_the_accepted_algorithms_are_a_fixed_literal():
    """The list must not be read from configuration or a token header."""
    import jwt_tokens

    source = inspect.getsource(jwt_tokens)

    assert 'algorithms=["HS256"]' in source or "algorithms=[ALGORITHM]" in source
    assert "algorithms=os.getenv" not in source
    assert "algorithms=settings" not in source


def test_signature_verification_is_never_disabled():
    """No code path may turn the check off, by flag or by option."""
    import apis.auth.utils.jwt_auth as jwt_auth
    import jwt_tokens

    for module in (jwt_auth, jwt_tokens):
        source = inspect.getsource(module)
        assert "verify_signature" not in source or (
            '"verify_signature": False' not in source
            and "'verify_signature': False" not in source
        )
        assert "VERIFY_SIGNATURE = False" not in source


def test_a_token_signed_with_another_key_is_rejected(anon_client):
    forged = jwt.encode(
        {
            "sub": "chef",
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        },
        "a-completely-different-key-of-sufficient-length",
        algorithm="HS256",
    )

    response = anon_client.get(
        "/admin/stats/disk", headers={"Authorization": f"Bearer {forged}"}
    )

    assert response.status_code == 401
