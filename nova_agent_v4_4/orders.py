"""Dummy order lookup stub."""
from typing import Union

def lookup_order(order_id: str) -> Union[dict, None]:
    # Replace with real DB/API call
    if order_id == "TEST123":
        return {"status": "shipped", "eta": "2025-07-02"}
    return None
