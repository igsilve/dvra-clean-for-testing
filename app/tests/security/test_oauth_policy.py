"""T1887: only safe OAuth 2.0 flows, and no way to pick an unsafe one.

The service uses no OAuth flow today, so the last test is the one that earns
its keep: it fails if flow code appears that does not go through the policy
module. The rest pin the policy's behaviour so the guard has something real
to point at.
"""

import pathlib

import pytest
from oauth_policy import (
    ALLOWED_FLOWS,
    AUTHORIZATION_CODE_PKCE,
    CLIENT_CREDENTIALS,
    DEVICE_FLOW,
    OAuthPolicyError,
    may_use_refresh_tokens,
    select_oauth_flow,
    validate_id_token_claims,
    validate_grant_payload,
)


@pytest.mark.security
def test_unsafe_flows_are_not_in_the_allowlist():
    assert "implicit" not in ALLOWED_FLOWS
    assert "password" not in ALLOWED_FLOWS
    assert ALLOWED_FLOWS == {
        AUTHORIZATION_CODE_PKCE,
        DEVICE_FLOW,
        CLIENT_CREDENTIALS,
    }


@pytest.mark.security
def test_browser_client_acting_for_a_user_gets_authorization_code_pkce():
    flow = select_oauth_flow(requires_user=True, is_confidential=False)
    assert flow == AUTHORIZATION_CODE_PKCE


@pytest.mark.security
def test_confidential_client_acting_for_a_user_also_gets_pkce():
    flow = select_oauth_flow(requires_user=True, is_confidential=True)
    assert flow == AUTHORIZATION_CODE_PKCE


@pytest.mark.security
def test_constrained_input_device_gets_the_device_flow_not_implicit():
    flow = select_oauth_flow(
        requires_user=True, is_confidential=False, constrained_input=True
    )
    assert flow == DEVICE_FLOW


@pytest.mark.security
def test_machine_to_machine_gets_client_credentials():
    flow = select_oauth_flow(requires_user=False, is_confidential=True)
    assert flow == CLIENT_CREDENTIALS


@pytest.mark.security
def test_public_client_cannot_use_client_credentials():
    with pytest.raises(OAuthPolicyError):
        select_oauth_flow(requires_user=False, is_confidential=False)


@pytest.mark.security
def test_public_clients_may_not_send_a_client_secret():
    with pytest.raises(OAuthPolicyError):
        validate_grant_payload(
            AUTHORIZATION_CODE_PKCE,
            {"code_verifier": "v", "client_secret": "s"},
            is_confidential=False,
        )


@pytest.mark.security
def test_token_exchange_requires_the_code_verifier():
    """PKCE on the authorization request alone proves nothing."""
    with pytest.raises(OAuthPolicyError):
        validate_grant_payload(
            AUTHORIZATION_CODE_PKCE, {"code": "abc"}, is_confidential=True
        )


@pytest.mark.security
def test_pkce_requires_s256():
    with pytest.raises(OAuthPolicyError):
        validate_grant_payload(
            AUTHORIZATION_CODE_PKCE,
            {"code_verifier": "v", "code_challenge_method": "plain"},
            is_confidential=True,
        )


@pytest.mark.security
def test_device_flow_requires_a_device_code():
    with pytest.raises(OAuthPolicyError):
        validate_grant_payload(DEVICE_FLOW, {}, is_confidential=False)


@pytest.mark.security
def test_an_unknown_flow_is_rejected():
    with pytest.raises(OAuthPolicyError):
        validate_grant_payload("implicit", {}, is_confidential=True)


@pytest.mark.security
def test_browser_clients_may_not_hold_refresh_tokens():
    assert may_use_refresh_tokens(is_confidential=True, is_browser=False)
    assert not may_use_refresh_tokens(is_confidential=True, is_browser=True)
    assert not may_use_refresh_tokens(is_confidential=False, is_browser=True)


@pytest.mark.security
def test_no_oauth_flow_code_bypasses_the_policy():
    """The guard: OAuth code must route through oauth_policy."""
    app_root = pathlib.Path(__file__).resolve().parents[2]

    markers = ("grant_type", "code_challenge", "response_type")

    offenders = []
    for path in app_root.rglob("*.py"):
        if "tests" in path.parts or path.name == "oauth_policy.py":
            continue
        text = path.read_text(encoding="utf-8")
        if not any(marker in text for marker in markers):
            continue
        if "oauth_policy" not in text:
            offenders.append(str(path.relative_to(app_root)))

    assert offenders == [], (
        f"OAuth flow code that bypasses oauth_policy: {offenders}"
    )


@pytest.mark.security
def test_the_implicit_grant_appears_nowhere():
    app_root = pathlib.Path(__file__).resolve().parents[2]

    offenders = []
    for path in app_root.rglob("*.py"):
        if "tests" in path.parts or path.name == "oauth_policy.py":
            continue
        text = path.read_text(encoding="utf-8")
        if 'response_type="token"' in text or "'implicit'" in text:
            offenders.append(str(path.relative_to(app_root)))

    assert offenders == [], f"implicit grant usage found: {offenders}"


# --- T1922: identity must come from validated claims ----------------------


@pytest.mark.security
@pytest.mark.parametrize("missing", ["iss", "sub", "aud", "exp", "iat"])
def test_id_token_missing_a_required_claim_is_rejected(missing):
    claims = {
        "iss": "https://issuer.example",
        "sub": "user-1",
        "aud": "this-client",
        "exp": 1,
        "iat": 0,
        "nonce": "n",
    }
    claims.pop(missing)

    with pytest.raises(OAuthPolicyError):
        validate_id_token_claims(
            claims,
            expected_issuer="https://issuer.example",
            expected_audience="this-client",
            expected_nonce="n",
        )


@pytest.mark.security
def test_id_token_from_another_issuer_or_for_another_client_is_rejected():
    base = {
        "iss": "https://issuer.example",
        "sub": "user-1",
        "aud": "this-client",
        "exp": 1,
        "iat": 0,
        "nonce": "n",
    }

    for wrong in ({"iss": "https://attacker.example"}, {"aud": "another-client"}):
        with pytest.raises(OAuthPolicyError):
            validate_id_token_claims(
                {**base, **wrong},
                expected_issuer="https://issuer.example",
                expected_audience="this-client",
                expected_nonce="n",
            )


@pytest.mark.security
def test_a_replayed_id_token_without_the_session_nonce_is_rejected():
    claims = {
        "iss": "https://issuer.example",
        "sub": "user-1",
        "aud": "this-client",
        "exp": 1,
        "iat": 0,
        "nonce": "someone-elses-session",
    }

    with pytest.raises(OAuthPolicyError):
        validate_id_token_claims(
            claims,
            expected_issuer="https://issuer.example",
            expected_audience="this-client",
            expected_nonce="our-session",
        )


@pytest.mark.security
def test_an_audience_list_containing_this_client_is_accepted():
    claims = {
        "iss": "https://issuer.example",
        "sub": "user-1",
        "aud": ["another-client", "this-client"],
        "exp": 1,
        "iat": 0,
        "nonce": "n",
    }

    assert validate_id_token_claims(
        claims,
        expected_issuer="https://issuer.example",
        expected_audience="this-client",
        expected_nonce="n",
    ) is claims


@pytest.mark.security
def test_identity_is_never_read_from_request_parameters():
    """The guard for T1922's central failure.

    A callback handler that lifts `sub` or `email` straight out of the
    query string trusts whatever the caller typed. No such handler exists
    today; this fails the build if one appears.
    """
    app_root = pathlib.Path(__file__).resolve().parents[2]

    sources = ("query_params", "request.args", "request.GET", "request.form")
    identity = ("id_token", "access_token", '"sub"', "'sub'", '"email"', "'email'")

    offenders = []
    for path in app_root.rglob("*.py"):
        if "tests" in path.parts or path.name == "oauth_policy.py":
            continue
        text = path.read_text(encoding="utf-8")
        if any(s in text for s in sources) and any(i in text for i in identity):
            offenders.append(str(path.relative_to(app_root)))

    assert offenders == [], (
        "identity or token material is being read from request parameters "
        f"in: {offenders}; it must come from a validated token result"
    )
