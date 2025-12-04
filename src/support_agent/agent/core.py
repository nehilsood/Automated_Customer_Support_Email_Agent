"""Main agent orchestrator for customer support."""

import json
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.agent.classifier import ClassificationResult, IntentClassifier
from support_agent.agent.prompts import get_agent_system_prompt, get_email_context_prompt
from support_agent.agent.router import ModelRouter
from support_agent.agent.tools.base import ToolRegistry, ToolResult
from support_agent.agent.tools.escalation import EscalateToHumanTool
from support_agent.agent.tools.knowledge_base import SearchKnowledgeBaseTool
from support_agent.agent.tools.shopify import (
    GetCustomerOrdersTool,
    GetFulfillmentTool,
    GetOrderTool,
)
from support_agent.integrations.openai_client import OpenAIClient
from support_agent.integrations.shopify.mock import MockShopifyClient


@dataclass
class AgentResponse:
    """Response from the support agent."""

    response_text: str
    classification: ClassificationResult
    tools_used: list[str]
    tool_results: list[dict]
    model_used: str
    tokens_input: int
    tokens_output: int
    response_time_ms: int
    escalated: bool = False
    escalation_reason: str | None = None


@dataclass
class ConversationMessage:
    """A message in the conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None


class SupportAgent:
    """Main agent orchestrator for handling customer support emails."""

    def __init__(
        self,
        db: AsyncSession,
        openai_client: OpenAIClient | None = None,
        shopify_client: MockShopifyClient | None = None,
    ):
        """Initialize the support agent.

        Args:
            db: Database session for tools.
            openai_client: OpenAI client instance.
            shopify_client: Shopify client instance.
        """
        self.db = db
        self.openai_client = openai_client or OpenAIClient()
        self.shopify_client = shopify_client or MockShopifyClient()

        # Initialize components
        self.classifier = IntentClassifier(self.openai_client)
        self.router = ModelRouter()

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools."""
        self.tool_registry.register(SearchKnowledgeBaseTool(self.db))
        self.tool_registry.register(GetOrderTool(self.shopify_client))
        self.tool_registry.register(GetFulfillmentTool(self.shopify_client))
        self.tool_registry.register(GetCustomerOrdersTool(self.shopify_client))
        self.tool_registry.register(EscalateToHumanTool(self.db))

    async def process_email(
        self,
        subject: str,
        body: str,
        sender_email: str,
        sender_name: str | None = None,
    ) -> AgentResponse:
        """Process a customer support email and generate a response.

        Args:
            subject: Email subject.
            body: Email body text.
            sender_email: Customer's email address.
            sender_name: Customer's name if known.

        Returns:
            AgentResponse with the generated response and metadata.
        """
        start_time = time.time()
        tools_used: list[str] = []
        tool_results: list[dict] = []

        # Step 1: Classify intent and complexity
        classification = await self.classifier.classify(
            subject=subject,
            body=body,
            sender_email=sender_email,
        )

        # Step 2: Check for immediate escalation
        if self.classifier.should_escalate(classification):
            escalation_result = await self._handle_immediate_escalation(
                classification=classification,
                sender_email=sender_email,
                subject=subject,
                body=body,
            )
            return AgentResponse(
                response_text=escalation_result["message"],
                classification=classification,
                tools_used=["escalate_to_human"],
                tool_results=[escalation_result],
                model_used="none",
                tokens_input=0,
                tokens_output=0,
                response_time_ms=int((time.time() - start_time) * 1000),
                escalated=True,
                escalation_reason=classification.reasoning,
            )

        # Step 3: Get model configuration based on complexity
        model_config = self.router.get_model_config(
            complexity=classification.complexity,
            intent=classification.intent,
        )

        # Step 4: Build conversation with system prompt
        messages = [
            {"role": "system", "content": get_agent_system_prompt()},
            {
                "role": "user",
                "content": get_email_context_prompt(
                    subject=subject,
                    body=body,
                    sender_email=sender_email,
                    sender_name=sender_name,
                ),
            },
        ]

        # Step 5: Run agent loop with tool calls
        total_input_tokens = 0
        total_output_tokens = 0
        max_iterations = 5  # Prevent infinite loops

        for iteration in range(max_iterations):
            # Call LLM with tools
            response = await self.openai_client.chat_completion(
                messages=messages,
                model=model_config.model,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                tools=self.tool_registry.get_openai_tools_schema(),
            )

            # Track token usage
            if response.usage:
                total_input_tokens += response.usage.prompt_tokens
                total_output_tokens += response.usage.completion_tokens

            assistant_message = response.choices[0].message

            # Check if model wants to use tools
            if assistant_message.tool_calls:
                # Add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                })

                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tools_used.append(tool_name)

                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Execute tool
                    result = await self.tool_registry.execute(tool_name, **tool_args)
                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result.to_dict(),
                    })

                    # Check for escalation
                    if tool_name == "escalate_to_human" and result.success:
                        return AgentResponse(
                            response_text=result.data.get("message", "Escalated to human agent."),
                            classification=classification,
                            tools_used=tools_used,
                            tool_results=tool_results,
                            model_used=model_config.model,
                            tokens_input=total_input_tokens,
                            tokens_output=total_output_tokens,
                            response_time_ms=int((time.time() - start_time) * 1000),
                            escalated=True,
                            escalation_reason=tool_args.get("reason", "Agent escalation"),
                        )

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result.to_dict()),
                    })
            else:
                # No tool calls, we have the final response
                response_text = assistant_message.content or "I apologize, I was unable to generate a response."
                break
        else:
            # Max iterations reached
            response_text = (
                "I apologize, but I'm having difficulty processing your request. "
                "Your inquiry has been forwarded to our support team for assistance."
            )

        return AgentResponse(
            response_text=response_text,
            classification=classification,
            tools_used=tools_used,
            tool_results=tool_results,
            model_used=model_config.model,
            tokens_input=total_input_tokens,
            tokens_output=total_output_tokens,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    async def _handle_immediate_escalation(
        self,
        classification: ClassificationResult,
        sender_email: str,
        subject: str,
        body: str,
    ) -> dict:
        """Handle immediate escalation without LLM call.

        Args:
            classification: Classification result.
            sender_email: Customer email.
            subject: Email subject.
            body: Email body.

        Returns:
            Escalation result dictionary.
        """
        escalation_tool = EscalateToHumanTool(self.db)
        result = await escalation_tool.execute(
            reason=f"Immediate escalation: {classification.intent.value}",
            priority="high" if classification.intent.value == "complaint" else "medium",
            customer_email=sender_email,
            summary=f"Subject: {subject}\n\nBody: {body[:500]}",
        )
        return result.data if result.success else {"message": "Your request has been escalated to our support team."}
