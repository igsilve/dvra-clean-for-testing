"""Remote content is checked before it is stored, not after.

The menu image feature fetches bytes from a host the caller names. Host
allow-listing and a pinned trust store (T558/T589) establish who we are
talking to; these tests cover the separate question of whether the bytes
that came back are the ones the caller reviewed.
"""

import io
from hashlib import sha256

import pytest
from apis.menu import utils
from apis.menu.schemas import MenuItemCreate
from config import settings
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import HTTPException
from PIL import Image
from pydantic import ValidationError

pytestmark = pytest.mark.security

TRUSTED_HOST = "cdn.restaurant.example"
TRUSTED_URL = f"https://{TRUSTED_HOST}/burger.png"
def _png() -> bytes:
    """A real PNG rather than a placeholder. The fetch path parses what it
    stores (T7366/T7381), so bytes that are not an image are refused before
    the digest question these tests are about."""
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), (1, 2, 3)).save(buffer, format="PNG")
    return buffer.getvalue()


IMAGE = _png()
IMAGE_DIGEST = sha256(IMAGE).hexdigest()


@pytest.fixture
def trusted_host(monkeypatch):
    monkeypatch.setattr(settings, "ALLOWED_IMAGE_HOSTS", [TRUSTED_HOST])
    monkeypatch.setattr(settings, "CDN_TOKEN", "")
    # The host name is deliberately one that does not exist, so the fetch
    # path's resolved-address check (T7360) would otherwise refuse it before
    # these tests reach the question they are about. Resolution is stubbed to
    # a routable address here; the check itself is exercised in
    # test_outbound_component_auth.py, where it is the subject.
    monkeypatch.setattr(
        utils.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )


@pytest.fixture
def signing_key(monkeypatch):
    """A publisher key, supplied the way the real one is: out of band."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setattr(
        settings, "CONTENT_SIGNING_PUBLIC_KEY_PEM", pem.decode()
    )
    return key


def _sign(key, content: bytes) -> str:
    import base64

    signature = key.sign(
        content,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


# --- T439: the digest ----------------------------------------------------


def test_content_matching_its_digest_is_accepted(trusted_host, requests_mock):
    requests_mock.get(TRUSTED_URL, content=IMAGE)

    encoded = utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)

    import base64

    assert base64.b64decode(encoded) == IMAGE


def test_substituted_content_is_rejected(trusted_host, requests_mock):
    """The host served something other than what the caller reviewed,
    which is what a compromised CDN or a stripped connection looks like."""
    requests_mock.get(TRUSTED_URL, content=b"something-else-entirely")

    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Content integrity check failed"


def test_a_single_flipped_byte_is_rejected(trusted_host, requests_mock):
    requests_mock.get(TRUSTED_URL, content=IMAGE + b"\x00")

    with pytest.raises(HTTPException):
        utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)


def test_nothing_is_returned_when_verification_fails(
    trusted_host, requests_mock
):
    """Verification happens before the bytes become a storable value, so a
    failure cannot leave partially-accepted content behind."""
    requests_mock.get(TRUSTED_URL, content=b"tampered")

    with pytest.raises(HTTPException):
        utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)


def test_a_url_without_a_digest_is_refused_at_the_schema():
    """Making the digest optional would make the control optional."""
    with pytest.raises(ValidationError) as exc:
        MenuItemCreate(
            name="Burger", price=9.5, category="main", image_url=TRUSTED_URL
        )

    assert "image_sha256 is required" in str(exc.value)


@pytest.mark.parametrize(
    "digest",
    [
        "not-a-digest",
        "ABCDEF" + "0" * 58,  # uppercase
        "0" * 63,  # too short
        "0" * 65,  # too long
    ],
)
def test_a_malformed_digest_is_refused(digest):
    with pytest.raises(ValidationError):
        MenuItemCreate(
            name="Burger",
            price=9.5,
            category="main",
            image_url=TRUSTED_URL,
            image_sha256=digest,
        )


def test_an_item_without_an_image_needs_no_digest():
    item = MenuItemCreate(name="Water", price=1.0, category="drink")

    assert item.image_sha256 is None


# --- T197: the signature -------------------------------------------------


def test_a_valid_signature_is_accepted(
    trusted_host, signing_key, requests_mock
):
    requests_mock.get(TRUSTED_URL, content=IMAGE)

    encoded = utils._image_url_to_base64(
        TRUSTED_URL, IMAGE_DIGEST, _sign(signing_key, IMAGE)
    )

    assert encoded


def test_content_signed_by_the_wrong_key_is_rejected(
    trusted_host, signing_key, requests_mock
):
    """The digest matches, so only the signature distinguishes a publisher
    we trust from one we do not."""
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    requests_mock.get(TRUSTED_URL, content=IMAGE)

    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(
            TRUSTED_URL, IMAGE_DIGEST, _sign(other_key, IMAGE)
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Content failed integrity verification"


def test_a_missing_signature_is_rejected_once_a_publisher_is_configured(
    trusted_host, signing_key, requests_mock
):
    requests_mock.get(TRUSTED_URL, content=IMAGE)

    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)

    assert exc.value.detail == "Content signature required"


def test_a_malformed_signature_is_rejected_not_raised_as_a_crash(
    trusted_host, signing_key, requests_mock
):
    requests_mock.get(TRUSTED_URL, content=IMAGE)

    with pytest.raises(HTTPException) as exc:
        utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST, "!!!not-base64")

    assert exc.value.status_code == 400


def test_the_verification_key_is_not_stored_with_the_content(trusted_host):
    """A key shipped alongside what it verifies proves nothing, so it comes
    from the environment rather than from the repository."""
    source = (
        __import__("pathlib")
        .Path(utils.__file__)
        .parent.joinpath("utils.py")
        .read_text()
    )

    assert "BEGIN PUBLIC KEY" not in source
    assert "CONTENT_SIGNING_PUBLIC_KEY_PEM" in source


def test_signature_checking_is_skipped_only_when_no_publisher_exists(
    trusted_host, requests_mock, monkeypatch
):
    """Verifying against an empty key would be theatre; the digest still
    has to hold."""
    monkeypatch.setattr(settings, "CONTENT_SIGNING_PUBLIC_KEY_PEM", "")
    requests_mock.get(TRUSTED_URL, content=IMAGE)

    assert utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)

    requests_mock.get(TRUSTED_URL, content=b"tampered")
    with pytest.raises(HTTPException):
        utils._image_url_to_base64(TRUSTED_URL, IMAGE_DIGEST)
