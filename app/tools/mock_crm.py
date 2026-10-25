
def get_order_status(order_id: str) -> dict:
    if not order_id:
        raise ValueError("order_id is required")

    orders = {
        "ORD-101": "Shipped",
        "ORD-102": "Processing",
        "ORD-103": "Delivered",
    }

    if order_id not in orders:
        raise ValueError(f"Order {order_id} was not found")

    return {
        "order_id": order_id,
        "status": orders[order_id],
    }
