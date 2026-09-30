"""Which OAuth 2.0 flows this service is permitted to use, and how.

This service is not an OAuth client today. It signs its own tokens in
`jwt_tokens` and issues them from `/token` against its own user store; there
is no identity provider, no client registration and no delegated
authorization anywhere in the codebase.

The module exists so that the decision is written down and enforced rather
than remembered. `tests/security/test_oauth_policy.py` fails the build if
OAuth flow code appears that does not route through `select_oauth_flow`,
which is what stops someone adding the implicit grant in a hurry two years
from now and nobody noticing until a token turns up in a URL fragment.

Note that `/token` uses FastAPI's OAuth2PasswordRequestForm, which has the
shape of the resource-owner-password grant. It is the application's own
login endpoint against its own user store, not a delegated OAuth flow, so
it is outside the scope of this selector. Federating authentication would
replace it rather than extend it.
"""

from typing import Mapping

# The only flows permitted. Implicit and resource-owner-password are absent
# deliberately: implicit returns tokens through the browser URL where they
# land in history and referrer headers, and password grant requires the
# client to handle the user's actual credentials.
AUTHORIZATION_CODE_PKCE = "authorization_code_pkce"
DEVICE_FLOW = "device_flow"
CLIENT_CREDENTIALS = "client_credentials"

ALLOWED_FLOWS = frozenset(
    {AUTHORIZATION_CODE_PKCE, DEVICE_FLOW, CLIENT_CREDENTIALS}
)

REQUIRED_CODE_CHALLENGE_METHOD = "S256"


class OAuthPolicyError(ValueError):
    """Raised when a flow or grant payload violates the policy."""


def select_oauth_flow(
    *,
    requires_user: bool,
    is_confidential: bool,
    constrained_input: bool = False,
) -> str:
    """Derive the flow from the client's traits, never from input.

    Taking the flow from a config string or a request parameter is how
    `implicit` gets back in, so there is no parameter here that names a
    flow. The caller describes the client; the policy decides.
    """
    if not requires_user:
        if not is_confidential:
            raise OAuthPolicyError(
                "client_credentials requires a confidential client"
            )
        return CLIENT_CREDENTIALS

    if constrained_input:
        return DEVICE_FLOW

    return AUTHORIZATION_CODE_PKCE


def may_use_refresh_tokens(*, is_confidential: bool, is_browser: bool) -> bool:
    """Browser-based clients have nowhere safe to keep a refresh token."""
    return is_confidential and not is_browser


def validate_grant_payload(
    flow: str, payload: Mapping[str, object], *, is_confidential: bool
) -> None:
    """Reject a token request that does not match its flow exactly."""
    if flow not in ALLOWED_FLOWS:
        raise OAuthPolicyError(f"flow {flow!r} is not permitted")

    if not is_confidential and "client_secret" in payload:
        # A secret shipped to a browser or a mobile binary is not a secret.
        raise OAuthPolicyError("public clients must not send a client_secret")

    if flow == AUTHORIZATION_CODE_PKCE:
        # PKCE only on the authorization request proves nothing; the token
        # exchange has to carry the matching verifier.
        if not payload.get("code_verifier"):
            raise OAuthPolicyError("authorization code exchange requires a code_verifier")
        if payload.get("code_challenge_method") not in (
            None,
            REQUIRED_CODE_CHALLENGE_METHOD,
        ):
            raise OAuthPolicyError("PKCE requires code_challenge_method=S256")

    if flow == DEVICE_FLOW and not payload.get("device_code"):
        raise OAuthPolicyError("device flow requires a device_code")

    if flow == CLIENT_CREDENTIALS and not is_confidential:
        raise OAuthPolicyError("client_credentials requires a confidential client")


# --- Identity claims -------------------------------------------------------
#
# If this service ever federates authentication, identity must come from a
# validated token result and nothing else. The failure this prevents is
# ordinary-looking: a callback handler reads `sub` or `email` out of the
# query string because they are right there, and the application trusts a
# value the caller typed.

REQUIRED_ID_TOKEN_CLAIMS = ("iss", "sub", "aud", "exp", "iat")


def validate_id_token_claims(
    claims: Mapping[str, object],
    *,
    expected_issuer: str,
    expected_audience: str,
    expected_nonce: str,
) -> Mapping[str, object]:
    """Check an ID token's claims before any of them are believed.

    The caller must pass claims that a library has already verified the
    signature of. This function does not verify signatures and must never
    be handed a decoded-but-unverified payload.
    """
    for claim in REQUIRED_ID_TOKEN_CLAIMS:
        if claim not in claims:
            raise OAuthPolicyError(f"id_token is missing the {claim} claim")

    if claims["iss"] != expected_issuer:
        raise OAuthPolicyError("id_token issuer does not match the provider")

    audience = claims["aud"]
    audiences = audience if isinstance(audience, (list, tuple)) else [audience]
    if expected_audience not in audiences:
        raise OAuthPolicyError("id_token was not issued for this client")

    # Without a nonce bound to the session, an id_token obtained elsewhere
    # can be replayed into someone else's login.
    if claims.get("nonce") != expected_nonce:
        raise OAuthPolicyError("id_token nonce does not match the session")

    return claims
