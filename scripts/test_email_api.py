#!/usr/bin/env python3
"""Test script for the Email API endpoints."""

import asyncio
import json
import sys

import httpx

BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Health Check")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_email_processing():
    """Test email processing endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Email Processing - Order Status")
    print("=" * 60)

    payload = {
        "from": "john.doe@example.com",
        "subject": "Where is my order?",
        "body": "Hi, I placed order #12345 last week and haven't received it yet. Can you tell me where it is?",
        "sender_name": "John Doe",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/email/process",
            json=payload,
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Intent: {data.get('intent')}")
        print(f"Complexity: {data.get('complexity')}")
        print(f"Tools Used: {data.get('tools_used')}")
        print(f"Model: {data.get('model_used')}")
        print(f"Response Time: {data.get('response_time_ms')}ms")
        print(f"Tokens: {data.get('tokens')}")
        print(f"Escalated: {data.get('escalated')}")
        print(f"Interaction ID: {data.get('interaction_id')}")
        print(f"\n--- Response ---\n{data.get('response_text')}")
        return response.status_code == 200


async def test_email_return_policy():
    """Test email processing with return policy question."""
    print("\n" + "=" * 60)
    print("TEST: Email Processing - Return Policy")
    print("=" * 60)

    payload = {
        "from": "customer@example.com",
        "subject": "Return policy question",
        "body": "What is your return policy? Can I return an item I bought 2 weeks ago?",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/email/process",
            json=payload,
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Intent: {data.get('intent')}")
        print(f"Complexity: {data.get('complexity')}")
        print(f"Tools Used: {data.get('tools_used')}")
        print(f"Model: {data.get('model_used')}")
        print(f"Response Time: {data.get('response_time_ms')}ms")
        print(f"Escalated: {data.get('escalated')}")
        print(f"\n--- Response ---\n{data.get('response_text')}")
        return response.status_code == 200


async def test_email_escalation():
    """Test email processing with escalation request."""
    print("\n" + "=" * 60)
    print("TEST: Email Processing - Escalation Request")
    print("=" * 60)

    payload = {
        "from": "angry@example.com",
        "subject": "I want to speak to a manager",
        "body": "This is ridiculous! I've been waiting for my refund for 3 weeks. I demand to speak to a supervisor immediately!",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/email/process",
            json=payload,
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Intent: {data.get('intent')}")
        print(f"Complexity: {data.get('complexity')}")
        print(f"Escalated: {data.get('escalated')}")
        print(f"Escalation Reason: {data.get('escalation_reason')}")
        print(f"\n--- Response ---\n{data.get('response_text')}")
        return response.status_code == 200


async def test_list_interactions():
    """Test listing interactions."""
    print("\n" + "=" * 60)
    print("TEST: List Interactions")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/interactions",
            params={"limit": 5},
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total: {data.get('total')}")
        print(f"Showing: {len(data.get('interactions', []))}")

        for i, interaction in enumerate(data.get("interactions", [])[:3], 1):
            print(f"\n  [{i}] {interaction.get('id')[:8]}...")
            print(f"      From: {interaction.get('sender_email')}")
            print(f"      Subject: {interaction.get('subject')}")
            print(f"      Intent: {interaction.get('intent')}")

        return response.status_code == 200


async def test_list_escalations():
    """Test listing escalations."""
    print("\n" + "=" * 60)
    print("TEST: List Escalations")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/escalations",
            params={"limit": 5},
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total: {data.get('total')}")
        print(f"Showing: {len(data.get('escalations', []))}")

        for i, esc in enumerate(data.get("escalations", [])[:3], 1):
            print(f"\n  [{i}] {esc.get('id')[:8]}...")
            print(f"      Status: {esc.get('status')}")
            print(f"      Reason: {esc.get('reason')[:50]}...")

        return response.status_code == 200


async def test_filter_by_email():
    """Test filtering interactions by sender email."""
    print("\n" + "=" * 60)
    print("TEST: Filter Interactions by Sender Email")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/interactions",
            params={"sender_email": "john.doe@example.com", "limit": 5},
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total matching: {data.get('total')}")

        for i, interaction in enumerate(data.get("interactions", [])[:3], 1):
            print(f"\n  [{i}] Subject: {interaction.get('subject')}")
            print(f"      Intent: {interaction.get('intent')}")

        return response.status_code == 200


async def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# Email API Test Suite")
    print("#" * 60)

    results = []

    # Test health first
    results.append(("Health Check", await test_health()))

    # Test email processing
    results.append(("Email - Order Status", await test_email_processing()))
    results.append(("Email - Return Policy", await test_email_return_policy()))
    results.append(("Email - Escalation", await test_email_escalation()))

    # Test admin endpoints
    results.append(("List Interactions", await test_list_interactions()))
    results.append(("List Escalations", await test_list_escalations()))
    results.append(("Filter by Email", await test_filter_by_email()))

    # Summary
    print("\n" + "#" * 60)
    print("# Test Summary")
    print("#" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
