from fastapi import HTTPException


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
