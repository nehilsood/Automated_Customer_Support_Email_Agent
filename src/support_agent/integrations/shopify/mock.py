"""Mock Shopify client for local development."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Order:
    """Order data model."""

    id: str
    order_number: str
    customer_email: str
    customer_name: str
    status: str
    created_at: str
    total_price: str
    currency: str
    line_items: list[dict]
    shipping_address: dict
    fulfillment: dict | None


@dataclass
class Fulfillment:
    """Fulfillment data model."""

    status: str
    carrier: str | None
    tracking_number: str | None
    tracking_url: str | None
    shipped_at: str | None
    delivered_at: str | None = None
    estimated_delivery: str | None = None


class MockShopifyClient:
    """Mock Shopify client that uses local JSON data."""

    def __init__(self, data_path: Path | None = None):
        """Initialize mock client.

        Args:
            data_path: Path to sample_orders.json file.
        """
        if data_path is None:
            data_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "sample_orders.json"
        self.data_path = data_path
        self._orders: list[dict] | None = None

    def _load_orders(self) -> list[dict]:
        """Load orders from JSON file."""
        if self._orders is None:
            with open(self.data_path) as f:
                self._orders = json.load(f)
        return self._orders

    def _normalize_order_number(self, order_number: str) -> str:
        """Normalize order number for comparison.

        Args:
            order_number: Order number (may or may not include #).

        Returns:
            Normalized order number without #.
        """
        return order_number.lstrip("#").strip()

    async def get_order(self, order_number: str) -> Order | None:
        """Get order by order number.

        Args:
            order_number: Order number (e.g., "12345" or "#12345").

        Returns:
            Order object or None if not found.
        """
        orders = self._load_orders()
        normalized = self._normalize_order_number(order_number)

        for order_data in orders:
            order_num = self._normalize_order_number(order_data["order_number"])
            if order_num == normalized:
                return Order(
                    id=order_data["id"],
                    order_number=order_data["order_number"],
                    customer_email=order_data["customer_email"],
                    customer_name=order_data["customer_name"],
                    status=order_data["status"],
                    created_at=order_data["created_at"],
                    total_price=order_data["total_price"],
                    currency=order_data["currency"],
                    line_items=order_data["line_items"],
                    shipping_address=order_data["shipping_address"],
                    fulfillment=order_data.get("fulfillment"),
                )
        return None

    async def get_order_by_id(self, order_id: str) -> Order | None:
        """Get order by internal ID.

        Args:
            order_id: Internal order ID (e.g., "ORD-12345").

        Returns:
            Order object or None if not found.
        """
        orders = self._load_orders()

        for order_data in orders:
            if order_data["id"] == order_id:
                return Order(
                    id=order_data["id"],
                    order_number=order_data["order_number"],
                    customer_email=order_data["customer_email"],
                    customer_name=order_data["customer_name"],
                    status=order_data["status"],
                    created_at=order_data["created_at"],
                    total_price=order_data["total_price"],
                    currency=order_data["currency"],
                    line_items=order_data["line_items"],
                    shipping_address=order_data["shipping_address"],
                    fulfillment=order_data.get("fulfillment"),
                )
        return None

    async def get_fulfillment(self, order_number: str) -> Fulfillment | None:
        """Get fulfillment info for an order.

        Args:
            order_number: Order number.

        Returns:
            Fulfillment object or None if not fulfilled.
        """
        order = await self.get_order(order_number)
        if not order or not order.fulfillment:
            return None

        f = order.fulfillment
        return Fulfillment(
            status=f["status"],
            carrier=f.get("carrier"),
            tracking_number=f.get("tracking_number"),
            tracking_url=f.get("tracking_url"),
            shipped_at=f.get("shipped_at"),
            delivered_at=f.get("delivered_at"),
            estimated_delivery=f.get("estimated_delivery"),
        )

    async def get_customer_orders(
        self, customer_email: str, limit: int = 10
    ) -> list[Order]:
        """Get all orders for a customer.

        Args:
            customer_email: Customer email address.
            limit: Maximum number of orders to return.

        Returns:
            List of Order objects.
        """
        orders = self._load_orders()
        customer_orders = []

        for order_data in orders:
            if order_data["customer_email"].lower() == customer_email.lower():
                customer_orders.append(
                    Order(
                        id=order_data["id"],
                        order_number=order_data["order_number"],
                        customer_email=order_data["customer_email"],
                        customer_name=order_data["customer_name"],
                        status=order_data["status"],
                        created_at=order_data["created_at"],
                        total_price=order_data["total_price"],
                        currency=order_data["currency"],
                        line_items=order_data["line_items"],
                        shipping_address=order_data["shipping_address"],
                        fulfillment=order_data.get("fulfillment"),
                    )
                )

        # Sort by created_at descending (most recent first)
        customer_orders.sort(key=lambda x: x.created_at, reverse=True)
        return customer_orders[:limit]

    def order_to_dict(self, order: Order) -> dict[str, Any]:
        """Convert Order to dictionary for serialization.

        Args:
            order: Order object.

        Returns:
            Dictionary representation.
        """
        return {
            "id": order.id,
            "order_number": order.order_number,
            "customer_email": order.customer_email,
            "customer_name": order.customer_name,
            "status": order.status,
            "created_at": order.created_at,
            "total_price": order.total_price,
            "currency": order.currency,
            "line_items": order.line_items,
            "shipping_address": order.shipping_address,
            "fulfillment": order.fulfillment,
        }

    def fulfillment_to_dict(self, fulfillment: Fulfillment) -> dict[str, Any]:
        """Convert Fulfillment to dictionary for serialization.

        Args:
            fulfillment: Fulfillment object.

        Returns:
            Dictionary representation.
        """
        return {
            "status": fulfillment.status,
            "carrier": fulfillment.carrier,
            "tracking_number": fulfillment.tracking_number,
            "tracking_url": fulfillment.tracking_url,
            "shipped_at": fulfillment.shipped_at,
            "delivered_at": fulfillment.delivered_at,
            "estimated_delivery": fulfillment.estimated_delivery,
        }
