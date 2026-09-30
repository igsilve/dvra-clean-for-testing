"""The single place where JSON Web Tokens are issued and verified.

Every issuing and verifying path in the application goes through this module.
The algorithm and the decode options were previously spelled out separately in
`apis/auth/utils/utils.py`, `apis/auth/utils/jwt_auth.py` and
`rate_limiting.py`; three copies of the same constant is three chances for one
of them to be loosened without the others.

The algorithm is a literal here and is never read from the token's own header,
so a caller cannot nominate `none` or swap in an algorithm whose key format
lets a public value be used as a MAC secret.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import settings
from jose import jwt

ALGORITHM = "HS256"

DEFAULT_EXPIRY = timedelta(minutes=15)

# The caller may ask for a shorter life than the default but not a longer one.
# Lifetime is the whole of a stateless token's exposure window: it is honoured
# until it expires no matter what happens to the account in the meantime, and
# revocation only takes effect when the holder next presents it. A call site
# passing a generous timedelta, or one computed from a request, is how a
# fifteen-minute credential quietly becomes a permanent one.
MAX_EXPIRY = timedelta(minutes=60)

# Verification is unconditional. python-jose expresses claim-presence checks
# as require_* booleans and ignores option keys it does not recognise, so a
# PyJWT-style {"require": ["exp", "sub"]} would be silently discarded and a
# token carrying no exp would be accepted as valid forever.
#
# iss and aud are required as well as validated: requiring presence is what
# stops a token minted before these claims existed from being accepted, and
# validating the values is what stops a token issued for a different
# audience being replayed here.
DECODE_OPTIONS = {
    "verify_signature": True,
    "verify_exp": True,
    "require_exp": True,
    "require_sub": True,
    "require_iat": True,
    "require_jti": True,
    "require_iss": True,
    "require_aud": True,
}


def encode_token(claims: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Issue a signed token with a unique identifier and full claim set.

    `jti` makes two tokens for the same user distinguishable even when issued
    in the same second, which `iat` alone does not guarantee.
    """
    now = datetime.now(timezone.utc)
    requested = expires_delta or DEFAULT_EXPIRY
    # min() rather than a rejection: a caller asking for too long is a bug to
    # be capped, not a reason to fail a user's sign-in.
    lifetime = min(requested, MAX_EXPIRY)
    to_encode = dict(claims)
    to_encode.update(
        {
            "exp": now + lifetime,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }
    )

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def invalidate_issued_tokens(user) -> None:
    """Revoke every token already issued for this user.

    Called after a credential or privilege change. The caller is responsible
    for committing; this only advances the counter that tokens are checked
    against, which is the stateless equivalent of deleting the old session.
    """
    user.token_version = (user.token_version or 0) + 1


def decode_token(token: str) -> dict:
    """Verify a token and return its claims, raising JWTError if invalid."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[ALGORITHM],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
        options=DECODE_OPTIONS,
    )
