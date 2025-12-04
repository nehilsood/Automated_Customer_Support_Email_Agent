"""Shopify tools for order and fulfillment lookups."""

from support_agent.agent.tools.base import BaseTool, ToolResult
from support_agent.integrations.shopify.mock import MockShopifyClient


class GetOrderTool(BaseTool):
    """Tool for getting order details by order number."""

    name = "get_order"
    description = (
        "Look up an order by its order number to get details like status, items, "
        "total price, and shipping address. Use this when a customer asks about "
        "their order status or order details."
    )
    parameters = {
        "type": "object",
        "properties": {
            "order_number": {
                "type": "string",
                "description": "The order number (e.g., '12345' or '#12345')",
            },
        },
        "required": ["order_number"],
    }

    def __init__(self, shopify_client: MockShopifyClient | None = None):
        """Initialize with Shopify client.

        Args:
            shopify_client: Shopify client instance (defaults to mock).
        """
        self.client = shopify_client or MockShopifyClient()

    async def execute(self, order_number: str, **kwargs) -> ToolResult:
        """Get order by order number.

        Args:
            order_number: Order number to look up.

        Returns:
            ToolResult with order details.
        """
        try:
            order = await self.client.get_order(order_number)

            if not order:
                return ToolResult(
                    success=True,
                    data={
                        "found": False,
                        "message": f"No order found with number {order_number}. "
                        "Please verify the order number and try again.",
                    },
                )

            return ToolResult(
                success=True,
                data={
                    "found": True,
                    "order": self.client.order_to_dict(order),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to retrieve order: {str(e)}",
            )


class GetFulfillmentTool(BaseTool):
    """Tool for getting shipping/tracking information."""

    name = "get_fulfillment"
    description = (
        "Get shipping and tracking information for an order. Use this when a customer "
        "asks about shipping status, tracking number, or delivery date."
    )
    parameters = {
        "type": "object",
        "properties": {
            "order_number": {
                "type": "string",
                "description": "The order number to get fulfillment info for",
            },
        },
        "required": ["order_number"],
    }

    def __init__(self, shopify_client: MockShopifyClient | None = None):
        """Initialize with Shopify client.

        Args:
            shopify_client: Shopify client instance (defaults to mock).
        """
        self.client = shopify_client or MockShopifyClient()

    async def execute(self, order_number: str, **kwargs) -> ToolResult:
        """Get fulfillment info for an order.

        Args:
            order_number: Order number.

        Returns:
            ToolResult with fulfillment details.
        """
        try:
            # First check if order exists
            order = await self.client.get_order(order_number)

            if not order:
                return ToolResult(
                    success=True,
                    data={
                        "found": False,
                        "message": f"No order found with number {order_number}.",
                    },
                )

            fulfillment = await self.client.get_fulfillment(order_number)

            if not fulfillment:
                return ToolResult(
                    success=True,
                    data={
                        "found": True,
                        "fulfilled": False,
                        "order_status": order.status,
                        "message": "This order has not been shipped yet. "
                        f"Current status: {order.status}.",
                    },
                )

            return ToolResult(
                success=True,
                data={
                    "found": True,
                    "fulfilled": True,
                    "fulfillment": self.client.fulfillment_to_dict(fulfillment),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to retrieve fulfillment info: {str(e)}",
            )


class GetCustomerOrdersTool(BaseTool):
    """Tool for getting all orders for a customer."""

    name = "get_customer_orders"
    description = (
        "Get all orders for a customer by their email address. Use this when a customer "
        "wants to see their order history or when you need to look up orders without "
        "a specific order number."
    )
    parameters = {
        "type": "object",
        "properties": {
            "customer_email": {
                "type": "string",
                "description": "The customer's email address",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of orders to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["customer_email"],
    }

    def __init__(self, shopify_client: MockShopifyClient | None = None):
        """Initialize with Shopify client.

        Args:
            shopify_client: Shopify client instance (defaults to mock).
        """
        self.client = shopify_client or MockShopifyClient()

    async def execute(
        self, customer_email: str, limit: int = 5, **kwargs
    ) -> ToolResult:
        """Get customer orders by email.

        Args:
            customer_email: Customer email address.
            limit: Maximum orders to return.

        Returns:
            ToolResult with order list.
        """
        try:
            orders = await self.client.get_customer_orders(customer_email, limit=limit)

            if not orders:
                return ToolResult(
                    success=True,
                    data={
                        "found": False,
                        "orders": [],
                        "message": f"No orders found for {customer_email}.",
                    },
                )

            return ToolResult(
                success=True,
                data={
                    "found": True,
                    "orders": [self.client.order_to_dict(o) for o in orders],
                    "count": len(orders),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to retrieve customer orders: {str(e)}",
            )
