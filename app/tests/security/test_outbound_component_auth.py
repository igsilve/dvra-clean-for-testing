"""T558 / T589: authenticate the remote component before trusting it.

Both outbound integrations are covered: the image fetch and the delivery
service. The shape of the risk is the same in each case — a call that names
no specific peer, presents no credential and accepts whatever comes back is
indistinguishable from a call to an attacker.
"""

import io
import socket
from hashlib import sha256

import pytest
import requests
from apis.menu import utils as menu_utils
from apis.menu.utils import _image_url_to_base64
from apis.orders.utils import (
    DeliveryStatus,
    fetch_order_status_from_delivery_service,
)
from config import settings
from fastapi import HTTPException
from PIL import Image
from pydantic import ValidationError

# The host checks run before anything is fetched, so these cases never
# reach the digest comparison.
ANY_DIGEST = "0" * 64

TRUSTED_HOST = "cdn.restaurant.example"
TRUSTED_URL = f"https://{TRUSTED_HOST}/burger.png"


def _png(width: int = 2, height: int = 2) -> bytes:
    """A real PNG. The fetch path parses what it stores (T7366/T7381), so a
    placeholder byte string is no longer accepted and should not be."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (1, 2, 3)).save(buffer, format="PNG")
    return buffer.getvalue()


PNG_BYTES = _png()


@pytest.fixture
def trusted_image_host(monkeypatch):
    monkeypatch.setattr(settings, "ALLOWED_IMAGE_HOSTS", [TRUSTED_HOST])
    monkeypatch.setattr(settings, "CDN_TOKEN", "cdn-secret-token")


@pytest.fixture
def configured_delivery_service(monkeypatch):
    monkeypatch.setattr(
        settings, "DELIVERY_API_BASE", "https://delivery.example/api"
    )
    monkeypatch.setattr(settings, "DELIVERY_API_TOKEN", "delivery-secret-token")


# --------------------------------------------------------------------------
# T558: image fetch
# --------------------------------------------------------------------------


@pytest.mark.security
@pytest.mark.parametrize(
    "url",
    [
        "http://cdn.restaurant.example/burger.png",  # not TLS
        "https://evil.example/burger.png",  # not on the allow-list
        "https://127.0.0.1/burger.png",  # loopback
        "https://169.254.169.254/latest/meta-data/",  # cloud metadata
        "file:///etc/passwd",
    ],
)
def test_untrusted_image_hosts_are_refused(url, trusted_image_host):
    with pytest.raises(HTTPException) as exc:
        _image_url_to_base64(url, ANY_DIGEST)

    assert exc.value.status_code == 400


@pytest.mark.security
def test_image_fetch_is_disabled_when_no_host_is_configured(monkeypatch):
    """An empty allow-list must mean "off", not "anything"."""
    monkeypatch.setattr(settings, "ALLOWED_IMAGE_HOSTS", [])

    with pytest.raises(HTTPException) as exc:
        _image_url_to_base64(TRUSTED_URL, ANY_DIGEST)

    assert exc.value.status_code == 400


@pytest.fixture
def resolving_to(monkeypatch):
    """Control what the allow-listed name resolves to.

    Separate from `trusted_image_host` on purpose. The refusal tests above
    pass literal addresses, which the name allow-list rejects before anything
    resolves, so stubbing the resolver in the shared fixture would hide the
    address check from the tests that are about it.
    """

    def _resolve(*addresses):
        monkeypatch.setattr(
            menu_utils.socket,
            "getaddrinfo",
            lambda *args, **kwargs: [
                (2, 1, 6, "", (address, 443)) for address in addresses
            ],
        )

    return _resolve


# --- T7360: the target is checked after resolution, not just as text ---


@pytest.mark.security
@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",  # loopback
        "169.254.169.254",  # cloud metadata
        "10.0.0.5",  # private
        "192.168.1.1",  # private
        "172.16.0.1",  # private
        "0.0.0.0",  # unspecified
        "::1",  # loopback, v6
        "fd00::1",  # private, v6
    ],
)
def test_an_allowed_name_resolving_inside_the_network_is_refused(
    trusted_image_host, resolving_to, address
):
    """The name allow-list is only as trustworthy as the DNS answer for it.

    A URL check cannot see this: the host is one this service was configured
    to trust, and the record for it points at something that was never meant
    to be reachable from outside. That is the request-forgery case.
    """
    resolving_to(address)

    with pytest.raises(HTTPException) as exc:
        _image_url_to_base64(TRUSTED_URL, ANY_DIGEST)

    assert exc.value.status_code == 400


@pytest.mark.security
def test_every_resolved_address_is_checked_not_only_the_first(
    trusted_image_host, resolving_to
):
    """Otherwise the outcome depends on the order the resolver happened to
    return, which an attacker controlling the record also controls."""
    resolving_to("93.184.216.34", "169.254.169.254")

    with pytest.raises(HTTPException) as exc:
        _image_url_to_base64(TRUSTED_URL, ANY_DIGEST)

    assert exc.value.status_code == 400


@pytest.mark.security
def test_a_name_that_does_not_resolve_is_refused(trusted_image_host, monkeypatch):
    """Fail closed: a resolution error must not skip the address check."""

    def _fail(*args, **kwargs):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(menu_utils.socket, "getaddrinfo", _fail)

    with pytest.raises(HTTPException) as exc:
        _image_url_to_base64(TRUSTED_URL, ANY_DIGEST)

    assert exc.value.status_code == 400


@pytest.mark.security
def test_the_address_is_checked_before_the_request_is_made(
    trusted_image_host, resolving_to, mocker
):
    """A check performed on the response is a check performed too late."""
    resolving_to("169.254.169.254")
    spy = mocker.spy(requests, "get")

    with pytest.raises(HTTPException):
        _image_url_to_base64(TRUSTED_URL, ANY_DIGEST)

    assert spy.call_count == 0


@pytest.mark.security
def test_image_fetch_presents_its_credential_over_a_pinned_trust_store(
    trusted_image_host, resolving_to, requests_mock, mocker
):
    import certifi

    resolving_to("93.184.216.34")
    requests_mock.get(TRUSTED_URL, content=PNG_BYTES)
    spy = mocker.spy(requests, "get")

    _image_url_to_base64(TRUSTED_URL, sha256(PNG_BYTES).hexdigest())

    kwargs = spy.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer cdn-secret-token"
    assert kwargs["verify"] == certifi.where()
    assert kwargs["allow_redirects"] is False
    assert kwargs["timeout"]


# --------------------------------------------------------------------------
# T589: delivery service
# --------------------------------------------------------------------------


@pytest.mark.security
def test_delivery_call_is_refused_when_unconfigured(monkeypatch):
    """No base URL or no token means the integration is off, not anonymous."""
    monkeypatch.setattr(settings, "DELIVERY_API_BASE", "")
    monkeypatch.setattr(settings, "DELIVERY_API_TOKEN", "")

    with pytest.raises(HTTPException) as exc:
        fetch_order_status_from_delivery_service(1)

    assert exc.value.status_code == 503


@pytest.mark.security
def test_delivery_call_requires_tls(monkeypatch):
    monkeypatch.setattr(settings, "DELIVERY_API_BASE", "http://delivery.example/api")
    monkeypatch.setattr(settings, "DELIVERY_API_TOKEN", "token")

    with pytest.raises(HTTPException) as exc:
        fetch_order_status_from_delivery_service(1)

    assert exc.value.status_code == 503


@pytest.mark.security
def test_delivery_call_presents_a_credential_and_pins_the_trust_store(
    configured_delivery_service, requests_mock, mocker
):
    import certifi

    requests_mock.get(
        "https://delivery.example/api/orders/7",
        json={"order_id": 7, "status": "ON_THE_WAY", "delivery_notes": "soon"},
    )
    spy = mocker.spy(requests, "get")

    result = fetch_order_status_from_delivery_service(7)

    kwargs = spy.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer delivery-secret-token"
    assert kwargs["verify"] == certifi.where()
    assert kwargs["allow_redirects"] is False
    assert result["status"] == "ON_THE_WAY"


@pytest.mark.security
def test_a_malformed_delivery_response_aborts_the_operation(
    configured_delivery_service, requests_mock
):
    requests_mock.get(
        "https://delivery.example/api/orders/8", json={"unexpected": "shape"}
    )

    with pytest.raises(HTTPException) as exc:
        fetch_order_status_from_delivery_service(8)

    assert exc.value.status_code == 502


@pytest.mark.security
def test_extra_fields_in_the_delivery_response_are_rejected(
    configured_delivery_service, requests_mock
):
    """A strict schema stops an unexpected field riding along into the order."""
    requests_mock.get(
        "https://delivery.example/api/orders/9",
        json={
            "order_id": 9,
            "status": "ON_THE_WAY",
            "delivery_notes": "",
            "is_admin": True,
        },
    )

    with pytest.raises(HTTPException) as exc:
        fetch_order_status_from_delivery_service(9)

    assert exc.value.status_code == 502


@pytest.mark.security
def test_a_reply_about_a_different_order_is_rejected(
    configured_delivery_service, requests_mock
):
    requests_mock.get(
        "https://delivery.example/api/orders/10",
        json={"order_id": 999, "status": "ON_THE_WAY", "delivery_notes": ""},
    )

    with pytest.raises(HTTPException) as exc:
        fetch_order_status_from_delivery_service(10)

    assert exc.value.status_code == 502


@pytest.mark.security
def test_a_transport_failure_aborts_rather_than_returning_a_default(
    configured_delivery_service, requests_mock
):
    requests_mock.get(
        "https://delivery.example/api/orders/11",
        exc=requests.exceptions.SSLError("certificate verify failed"),
    )

    with pytest.raises(HTTPException) as exc:
        fetch_order_status_from_delivery_service(11)

    assert exc.value.status_code == 502


@pytest.mark.security
def test_delivery_schema_forbids_extra_fields():
    with pytest.raises(ValidationError):
        DeliveryStatus.model_validate(
            {"order_id": 1, "status": "ON_THE_WAY", "surprise": 1}
        )
