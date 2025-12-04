#!/usr/bin/env python3
"""Test script for the support agent."""

import asyncio
import json

from support_agent.agent.core import SupportAgent
from support_agent.integrations.database.connection import get_db_session


async def test_order_status():
    """Test order status inquiry."""
    print("\n" + "=" * 60)
    print("TEST 1: Order Status Inquiry")
    print("=" * 60)

    async with get_db_session() as db:
        agent = SupportAgent(db)
        response = await agent.process_email(
            subject="Where is my order?",
            body="Hi, I placed order #12345 last week and haven't received it yet. Can you tell me where it is?",
            sender_email="john.doe@example.com",
            sender_name="John Doe",
        )

        print(f"\nIntent: {response.classification.intent.value}")
        print(f"Complexity: {response.classification.complexity.value}")
        print(f"Model Used: {response.model_used}")
        print(f"Tools Used: {response.tools_used}")
        print(f"Response Time: {response.response_time_ms}ms")
        print(f"Tokens: {response.tokens_input} in, {response.tokens_output} out")
        print(f"\n--- Response ---\n{response.response_text}")


async def test_return_policy():
    """Test return policy question."""
    print("\n" + "=" * 60)
    print("TEST 2: Return Policy Question")
    print("=" * 60)

    async with get_db_session() as db:
        agent = SupportAgent(db)
        response = await agent.process_email(
            subject="Return policy",
            body="What is your return policy? Can I return an item I bought 2 weeks ago?",
            sender_email="customer@example.com",
        )

        print(f"\nIntent: {response.classification.intent.value}")
        print(f"Complexity: {response.classification.complexity.value}")
        print(f"Model Used: {response.model_used}")
        print(f"Tools Used: {response.tools_used}")
        print(f"Response Time: {response.response_time_ms}ms")
        print(f"\n--- Response ---\n{response.response_text}")


async def test_shipping_tracking():
    """Test shipping tracking inquiry."""
    print("\n" + "=" * 60)
    print("TEST 3: Shipping Tracking")
    print("=" * 60)

    async with get_db_session() as db:
        agent = SupportAgent(db)
        response = await agent.process_email(
            subject="Tracking number please",
            body="Can I get the tracking number for order #12346? I want to know when it will arrive.",
            sender_email="jane.smith@example.com",
            sender_name="Jane Smith",
        )

        print(f"\nIntent: {response.classification.intent.value}")
        print(f"Complexity: {response.classification.complexity.value}")
        print(f"Model Used: {response.model_used}")
        print(f"Tools Used: {response.tools_used}")
        print(f"Response Time: {response.response_time_ms}ms")
        print(f"\n--- Response ---\n{response.response_text}")


async def test_customer_orders():
    """Test customer order history lookup."""
    print("\n" + "=" * 60)
    print("TEST 4: Customer Order History")
    print("=" * 60)

    async with get_db_session() as db:
        agent = SupportAgent(db)
        response = await agent.process_email(
            subject="My orders",
            body="Can you show me all my recent orders? I can't remember which one I need to return.",
            sender_email="john.doe@example.com",
            sender_name="John Doe",
        )

        print(f"\nIntent: {response.classification.intent.value}")
        print(f"Complexity: {response.classification.complexity.value}")
        print(f"Model Used: {response.model_used}")
        print(f"Tools Used: {response.tools_used}")
        print(f"Response Time: {response.response_time_ms}ms")
        print(f"\n--- Response ---\n{response.response_text}")


async def test_escalation():
    """Test escalation request."""
    print("\n" + "=" * 60)
    print("TEST 5: Escalation Request")
    print("=" * 60)

    async with get_db_session() as db:
        agent = SupportAgent(db)
        response = await agent.process_email(
            subject="I want to speak to a manager",
            body="This is ridiculous! I've been waiting for my refund for 3 weeks. I demand to speak to a supervisor immediately!",
            sender_email="angry@example.com",
        )

        print(f"\nIntent: {response.classification.intent.value}")
        print(f"Complexity: {response.classification.complexity.value}")
        print(f"Escalated: {response.escalated}")
        print(f"Escalation Reason: {response.escalation_reason}")
        print(f"Response Time: {response.response_time_ms}ms")
        print(f"\n--- Response ---\n{response.response_text}")


async def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# Support Agent Test Suite")
    print("#" * 60)

    await test_order_status()
    await test_return_policy()
    await test_shipping_tracking()
    await test_customer_orders()
    await test_escalation()

    print("\n" + "#" * 60)
    print("# All tests completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
