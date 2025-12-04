"""Intent classification for customer emails."""

import json
from dataclasses import dataclass
from enum import Enum

from support_agent.config import get_settings
from support_agent.integrations.openai_client import OpenAIClient


class Intent(str, Enum):
    """Customer email intent categories."""

    ORDER_STATUS = "order_status"
    SHIPPING_TRACKING = "shipping_tracking"
    RETURN_REQUEST = "return_request"
    REFUND_REQUEST = "refund_request"
    PRODUCT_QUESTION = "product_question"
    POLICY_QUESTION = "policy_question"
    COMPLAINT = "complaint"
    GENERAL_INQUIRY = "general_inquiry"
    ESCALATION_REQUEST = "escalation_request"


class Complexity(str, Enum):
    """Query complexity levels for tiered routing."""

    SIMPLE = "simple"  # Direct lookup, single tool call
    MEDIUM = "medium"  # Multiple tool calls, straightforward
    COMPLEX = "complex"  # Requires reasoning, multiple steps, or escalation


@dataclass
class ClassificationResult:
    """Result from intent classification."""

    intent: Intent
    complexity: Complexity
    confidence: float
    requires_order_lookup: bool
    requires_knowledge_base: bool
    suggested_tools: list[str]
    reasoning: str


CLASSIFICATION_PROMPT = """You are an intent classifier for a customer support system.
Analyze the customer email and classify it.

Customer Email:
Subject: {subject}
Body: {body}
From: {sender_email}

Classify this email and respond with a JSON object containing:
1. "intent": One of: order_status, shipping_tracking, return_request, refund_request,
   product_question, policy_question, complaint, general_inquiry, escalation_request
2. "complexity": One of:
   - "simple": Direct lookup or FAQ answer (single tool call)
   - "medium": Requires 2-3 tool calls or moderate reasoning
   - "complex": Requires multiple steps, sensitive issue, or should escalate
3. "confidence": Float 0-1 indicating classification confidence
4. "requires_order_lookup": Boolean - does this need order/fulfillment data?
5. "requires_knowledge_base": Boolean - does this need KB search?
6. "suggested_tools": List of tools to use: ["search_knowledge_base", "get_order",
   "get_fulfillment", "get_customer_orders", "escalate_to_human"]
7. "reasoning": Brief explanation of your classification

Classification guidelines:
- order_status: "Where is my order?", "Order status", "When will it arrive?"
- shipping_tracking: "Tracking number", "Track my package", "Shipping update"
- return_request: "Return", "Send back", "Wrong item"
- refund_request: "Refund", "Money back", "Charge dispute"
- product_question: Questions about products, sizes, features
- policy_question: Store policies, warranty, terms
- complaint: Negative feedback, dissatisfaction, problems
- escalation_request: "Speak to manager", "Human agent", "Supervisor"
- general_inquiry: Everything else

Complexity guidelines:
- SIMPLE: "What's the return policy?" (KB search only)
- SIMPLE: "Where is order #12345?" (Single order lookup)
- MEDIUM: "I want to return order #12345" (Order lookup + policy)
- COMPLEX: Complaints, refund requests > $100, multi-order issues

Respond ONLY with the JSON object, no other text."""


class IntentClassifier:
    """Classifies customer email intent and complexity."""

    def __init__(self, openai_client: OpenAIClient | None = None):
        """Initialize classifier.

        Args:
            openai_client: OpenAI client instance.
        """
        self.settings = get_settings()
        self.client = openai_client or OpenAIClient()

    async def classify(
        self,
        subject: str,
        body: str,
        sender_email: str,
    ) -> ClassificationResult:
        """Classify customer email intent and complexity.

        Args:
            subject: Email subject line.
            body: Email body text.
            sender_email: Sender's email address.

        Returns:
            ClassificationResult with intent, complexity, and suggested tools.
        """
        prompt = CLASSIFICATION_PROMPT.format(
            subject=subject,
            body=body,
            sender_email=sender_email,
        )

        response = await self.client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=self.settings.classifier_model,
            temperature=0.1,  # Low temperature for consistent classification
        )

        # Parse JSON response
        content = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback classification
            return ClassificationResult(
                intent=Intent.GENERAL_INQUIRY,
                complexity=Complexity.MEDIUM,
                confidence=0.5,
                requires_order_lookup=False,
                requires_knowledge_base=True,
                suggested_tools=["search_knowledge_base"],
                reasoning="Failed to parse classification, defaulting to general inquiry",
            )

        return ClassificationResult(
            intent=Intent(result.get("intent", "general_inquiry")),
            complexity=Complexity(result.get("complexity", "medium")),
            confidence=float(result.get("confidence", 0.8)),
            requires_order_lookup=bool(result.get("requires_order_lookup", False)),
            requires_knowledge_base=bool(result.get("requires_knowledge_base", True)),
            suggested_tools=result.get("suggested_tools", ["search_knowledge_base"]),
            reasoning=result.get("reasoning", ""),
        )

    def should_escalate(self, classification: ClassificationResult) -> bool:
        """Determine if this request should be escalated immediately.

        Args:
            classification: Classification result.

        Returns:
            True if immediate escalation is recommended.
        """
        # Immediate escalation conditions
        if classification.intent == Intent.ESCALATION_REQUEST:
            return True
        if classification.intent == Intent.COMPLAINT and classification.complexity == Complexity.COMPLEX:
            return True
        if classification.confidence < 0.5:
            return True
        return False
