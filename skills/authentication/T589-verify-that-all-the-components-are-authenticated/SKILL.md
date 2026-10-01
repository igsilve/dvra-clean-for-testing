---
name: t589-verify-that-all-the-components-are-authenticated-explicitly
description: Authenticate the delivery-service integration in both directions rather than trusting whatever the call returns.
---

# T589: Verify that all the components are authenticated explicitly

**Category:** CODE_FIX
**SD Elements:** [T589](https://staging.qa.sdelements.com/bunits/1101/projects/4560/tasks/4560-T589/)
**Priority:** 9

**Finding:** The delivery-service integration point returns data without authenticating the remote component.

**Code to Fix:**
```python
# app/apis/orders/utils.py lines 4-15
def fetch_order_status_from_delivery_service(order_id: int):
    """
    Simulates fetching order status from an external delivery service.
    In a real scenario, this would make an actual API call.
    """

    # In reality: response = requests.get(f"https://delivery.service/api/orders/{order_id}")
    return {
        "order_id": order_id,
        "status": "ON_THE_WAY",
        "delivery_notes": "Your order is on the way!",
    }
```

**Required Fix:**
```python
# app/apis/orders/utils.py
def fetch_order_status_from_delivery_service(order_id: int) -> dict:
    response = requests.get(
        f"{settings.DELIVERY_API_BASE}/orders/{order_id}",
        timeout=5,
        verify=True,
        headers={"Authorization": f"Bearer {settings.DELIVERY_API_TOKEN}"},
    )
    response.raise_for_status()
    payload = DeliveryStatus.model_validate(response.json())   # strict schema
    return payload.model_dump()
```

**Success Criteria:**
- The integration presents a credential and validates the peer certificate.
- The response is parsed through a strict schema before use.
- An unauthenticated or malformed response aborts the operation.

**Status:** Applied
