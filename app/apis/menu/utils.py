import base64
import io
import ipaddress
import logging
import socket
from hashlib import sha256
from hmac import compare_digest
from urllib.parse import urlparse

import certifi
import requests
from PIL import Image
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from apis.auth.utils.authz import AuthzContext, Permission
from apis.menu import schemas
from config import settings
from db.models import MenuItem, OrderItem
from fastapi import HTTPException


logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 2 * 1024 * 1024
IMAGE_FETCH_TIMEOUT = (3, 5)  # (connect, read) seconds

# Container formats whose parsers this service is prepared to run. Narrow on
# purpose: every additional format is another decoder reachable from a remote
# byte stream, and the menu needs none of them.
ALLOWED_IMAGE_FORMATS = frozenset({"JPEG", "PNG", "GIF", "WEBP"})

# Bounds the decompressed size rather than the transferred size. 32 megapixels
# is far more than a menu photograph needs and far less than a decompression
# bomb requires.
MAX_IMAGE_PIXELS = 32 * 1024 * 1024


def _assert_image_host_is_authenticated(image_url: str) -> None:
    """Refuse any image host this service has not been told to trust.

    Three things have to hold before a byte is exchanged: the peer is one we
    named in advance, the channel is TLS so its certificate can be checked
    at all, and we are in a position to present our own credential. Fetching
    from an arbitrary URL satisfies none of them, and also hands whoever
    supplies the URL a request originating inside the network.
    """
    parsed = urlparse(image_url)

    if parsed.scheme != "https":
        raise HTTPException(
            status_code=400, detail="Image host not allowed"
        )

    # An empty allow-list disables the feature rather than permitting
    # everything, so a missing configuration fails closed.
    if parsed.hostname not in settings.ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="Image host not allowed")

    _assert_resolved_address_is_routable(parsed.hostname)


def _assert_resolved_address_is_routable(hostname: str) -> None:
    """Refuse a host whose name resolves inside the infrastructure.

    The name allow-list is checked before this and is not enough on its own.
    A name on the list is only as trustworthy as the DNS answer for it, and an
    answer of 169.254.169.254 or 127.0.0.1 turns an allowed fetch into a read
    of the cloud metadata service or of something bound to localhost that was
    never meant to be reachable. That is the request-forgery case, and it is
    invisible to any check performed on the URL string.

    Every address the name resolves to is checked, not the first: a name with
    one public and one private answer would otherwise pass or fail depending
    on the order the resolver happened to return.

    This does not close the window between resolving here and the address the
    connection actually uses, which a short-TTL record can still move. What
    makes that acceptable is the allow-list in front of it -- an attacker
    needs to already control a name this service was configured to trust.
    """
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Image host not allowed")

    for family, _type, _proto, _canonname, sockaddr in resolved:
        address = ipaddress.ip_address(sockaddr[0])
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            logger.warning(
                "image host rejected: resolves to a non-routable address",
                extra={"host": hostname, "address": str(address)},
            )
            raise HTTPException(status_code=400, detail="Image host not allowed")


def _verify_content(content: bytes, expected_sha256: str, signature_b64) -> None:
    """Reject content that is not what the caller said it would be.

    Two separate questions, checked in order. The digest answers whether
    these are the bytes the caller reviewed, which a compromised image host
    or a stripped TLS connection would fail. The signature answers who
    produced them, which a caller who reviewed the wrong thing would fail.
    The digest is always required; the signature only when a publishing key
    has been configured, because verifying against no key is theatre.
    """
    actual = sha256(content).hexdigest()
    if not compare_digest(actual, expected_sha256):
        logger.warning(
            "remote content rejected: digest mismatch",
            extra={"expected": expected_sha256, "actual": actual},
        )
        raise HTTPException(status_code=400, detail="Content integrity check failed")

    public_key_pem = settings.CONTENT_SIGNING_PUBLIC_KEY_PEM
    if not public_key_pem:
        return

    if not signature_b64:
        raise HTTPException(status_code=400, detail="Content signature required")

    try:
        public_key = load_pem_public_key(public_key_pem.encode())
        public_key.verify(
            base64.b64decode(signature_b64),
            content,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except (InvalidSignature, ValueError, TypeError):
        logger.warning("remote content rejected: signature did not verify")
        raise HTTPException(
            status_code=400, detail="Content failed integrity verification"
        )


def _assert_content_is_a_supported_image(content: bytes) -> None:
    """Decide what the bytes are by parsing them, not by being told.

    A digest proves the bytes are the ones the caller meant; it says nothing
    about what they contain. Without this, an HTML document or a PHP script
    could be stored as `image_base64` and served back from the menu, where the
    only thing deciding how a browser treats it is a content type this service
    never set.

    Three separate limits, because each catches something the others do not:

    - the format allow-list rejects container types whose parsers are large
      and rarely exercised, before any of that code runs;
    - `verify()` fails closed on a truncated or malformed file rather than
      returning a partially decoded image;
    - MAX_IMAGE_PIXELS bounds the decompressed size, which the byte ceiling
      does not: a few kilobytes of valid PNG can declare dimensions that
      expand to gigabytes of pixels and exhaust the process.
    """
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    try:
        with Image.open(io.BytesIO(content)) as image:
            image_format = image.format
            # Reads the header only; the dimensions are checked before
            # anything decodes the pixel data.
            width, height = image.size

            if image_format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=400, detail="Unsupported image format"
                )

            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image too large")

            # Consumes the rest of the file and raises if it does not hold
            # together. An image that only parses as far as its header is
            # exactly what a malformed-input attack produces.
            image.verify()
    except HTTPException:
        raise
    except Image.DecompressionBombError:
        # Pillow raises this from open() when the declared dimensions are far
        # past the ceiling, before the explicit check below can run, so the
        # size case is reported as a size error rather than a format one.
        logger.warning("remote content rejected: declared dimensions too large")
        raise HTTPException(status_code=413, detail="Image too large")
    except Exception:
        # Pillow raises a wide range of types, most of them undocumented,
        # including UnidentifiedImageError and bare OSError. Anything it could
        # not parse is refused.
        logger.warning("remote content rejected: not a parseable image")
        raise HTTPException(status_code=400, detail="Unsupported image format")


def _image_url_to_base64(
    image_url: str, expected_sha256: str, signature_b64=None
) -> str:
    _assert_image_host_is_authenticated(image_url)

    headers = {}
    if settings.CDN_TOKEN:
        headers["Authorization"] = f"Bearer {settings.CDN_TOKEN}"

    with requests.get(
        image_url,
        stream=True,
        timeout=IMAGE_FETCH_TIMEOUT,
        allow_redirects=False,
        # Pinned to certifi's bundle rather than the ambient system store,
        # so a certificate added to the host cannot silently widen who this
        # service will trust.
        verify=certifi.where(),
        headers=headers,
    ) as response:
        # Checked before raise_for_status, which treats 3xx as success. With
        # redirects disabled a 302 returns an empty body that would otherwise
        # travel on to the digest check and fail there, reporting an integrity
        # problem for what is actually a misdirection attempt.
        if response.is_redirect or response.is_permanent_redirect:
            logger.warning(
                "image host attempted to redirect",
                extra={"location": response.headers.get("Location", "")},
            )
            raise HTTPException(
                status_code=400,
                detail="Redirects are not permitted for image sources",
            )

        response.raise_for_status()

        declared = response.headers.get("Content-Length")
        if declared is not None:
            try:
                if int(declared) > MAX_IMAGE_BYTES:
                    raise HTTPException(status_code=413, detail="Image too large")
            except ValueError:
                raise HTTPException(status_code=502, detail="Invalid image response")

        chunks, total = [], 0
        for chunk in response.iter_content(64 * 1024):
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=413, detail="Image too large")
            chunks.append(chunk)

    content = b"".join(chunks)
    # Before the bytes become a value the caller can persist, not after.
    _verify_content(content, expected_sha256, signature_b64)
    _assert_content_is_a_supported_image(content)

    return base64.b64encode(content).decode()


def create_menu_item(
    db,
    menu_item: schemas.MenuItemCreate,
    authz: AuthzContext,
):
    """Create a menu item.

    `authz` is required rather than optional: the permission is re-checked
    here, at the point the data actually changes, so a second caller that
    is not an HTTP route inherits the same rule instead of none.
    """
    authz.require(Permission.MANAGE_MENU)

    menu_item_dict = menu_item.dict()
    image_url = menu_item_dict.pop("image_url", None)
    expected_sha256 = menu_item_dict.pop("image_sha256", None)
    signature = menu_item_dict.pop("image_signature", None)
    db_item = MenuItem(**menu_item_dict)

    if image_url:
        db_item.image_base64 = _image_url_to_base64(
            image_url, expected_sha256, signature
        )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def update_menu_item(
    db,
    item_id: int,
    menu_item: schemas.MenuItemCreate,
    authz: AuthzContext,
):
    authz.require(Permission.MANAGE_MENU)

    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    menu_item_dict = menu_item.dict()
    image_url = menu_item_dict.pop("image_url", None)
    expected_sha256 = menu_item_dict.pop("image_sha256", None)
    signature = menu_item_dict.pop("image_signature", None)

    for key, value in menu_item_dict.items():
        setattr(db_item, key, value)

    if image_url:
        db_item.image_base64 = _image_url_to_base64(
            image_url, expected_sha256, signature
        )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_menu_item(db, item_id: int, authz: AuthzContext):
    authz.require(Permission.MANAGE_MENU)

    existing_order_item = (
        db.query(OrderItem).filter(OrderItem.menu_item_id == item_id).first()
    )
    if existing_order_item is not None:
        raise HTTPException(
            status_code=409,
            detail="You can not delete this menu item, it is associated with existing orders.",
        )

    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(db_item)
    db.commit()
