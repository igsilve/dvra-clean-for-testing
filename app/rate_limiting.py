import hashlib

from jose import JWTError
from jwt_tokens import decode_token
from slowapi import Limiter
from slowapi.util import get_remote_address


def identify_client(request) -> str:
    """Throttle per identity, falling back to the source address.

    Keying on the address alone lumps every user behind a NAT or proxy into a
    single bucket, and lets an authenticated attacker reset their budget by
    changing address. A verified token subject is used whenever one is present;
    an unverified or absent token never yields an identity key.
    """
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            subject = decode_token(token).get("sub")
        except JWTError:
            subject = None
        if subject:
            return "user:" + hashlib.sha256(subject.encode()).hexdigest()[:32]

    return "ip:" + get_remote_address(request)


# A default ceiling applies to every route; sensitive routes carry a tighter
# explicit @limiter.limit decorator on top of it.
limiter = Limiter(key_func=identify_client, default_limits=["120/minute"])
