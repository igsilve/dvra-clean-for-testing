"""Delivery-service integration.

The remote component is authenticated in both directions before its answer
is believed: TLS with a pinned trust store proves who the peer is, a bearer
credential proves who we are, and a strict schema means a peer that is
somehow not the one we expected still cannot feed arbitrary fields into the
order record.
"""

from urllib.parse import urlparse

import certifi
import requests
from config import settings
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, ValidationError


class DeliveryStatus(BaseModel):
    """Strict contract for the delivery service's reply.

    extra="forbid" so an unexpected field is an error rather than something
    that silently rides along into whatever consumes this.
    """

    model_config = ConfigDict(extra="forbid")

    order_id: int
    status: str
    delivery_notes: str = ""


def _delivery_endpoint(order_id: int) -> str:
    base = settings.DELIVERY_API_BASE

    # Unconfigured means the integration is off, not that it may be called
    # anonymously against some default host.
    if not base or not settings.DELIVERY_API_TOKEN:
        raise HTTPException(
            status_code=503, detail="Delivery service is not configured"
        )

    if urlparse(base).scheme != "https":
        raise HTTPException(
            status_code=503, detail="Delivery service is not configured"
        )

    return f"{base.rstrip('/')}/orders/{order_id}"


def fetch_order_status_from_delivery_service(order_id: int) -> dict:
    url = _delivery_endpoint(order_id)

    try:
        response = requests.get(
            url,
            timeout=settings.OUTBOUND_TIMEOUT,
            # Pinned trust store, and redirects refused so the peer cannot
            # send us somewhere that was never authenticated.
            verify=certifi.where(),
            allow_redirects=False,
            headers={"Authorization": f"Bearer {settings.DELIVERY_API_TOKEN}"},
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        raise HTTPException(
            status_code=502, detail="Delivery service is unavailable"
        )
    except ValueError:
        raise HTTPException(
            status_code=502, detail="Delivery service returned an invalid response"
        )

    try:
        status = DeliveryStatus.model_validate(payload)
    except ValidationError:
        raise HTTPException(
            status_code=502, detail="Delivery service returned an invalid response"
        )

    # The service is answering about the order we asked about, or it is not
    # answering about anything we should act on.
    if status.order_id != order_id:
        raise HTTPException(
            status_code=502, detail="Delivery service returned an invalid response"
        )

    return status.model_dump()
