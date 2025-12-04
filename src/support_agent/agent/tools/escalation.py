"""Escalation tool for routing complex issues to human agents."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.agent.tools.base import BaseTool, ToolResult
from support_agent.integrations.database.models import Escalation


class EscalateToHumanTool(BaseTool):
    """Tool for escalating issues to human support agents."""

    name = "escalate_to_human"
    description = (
        "Escalate a customer issue to a human support agent. Use this when: "
        "1) The customer explicitly requests to speak with a human, "
        "2) The issue is too complex to resolve automatically, "
        "3) The customer is frustrated or angry, "
        "4) The query involves sensitive matters like refunds over $100 or complaints, "
        "5) You cannot find relevant information to help the customer."
    )
    parameters = {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Brief explanation of why escalation is needed",
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
                "description": "Priority level based on issue severity",
            },
            "customer_email": {
                "type": "string",
                "description": "Customer's email address",
            },
            "summary": {
                "type": "string",
                "description": "Summary of the customer's issue and any actions already taken",
            },
        },
        "required": ["reason", "priority", "customer_email", "summary"],
    }

    def __init__(self, db: AsyncSession | None = None):
        """Initialize with optional database session.

        Args:
            db: Async database session for persisting escalations.
        """
        self.db = db

    async def execute(
        self,
        reason: str,
        priority: str,
        customer_email: str,
        summary: str,
        interaction_id: str | None = None,
        **kwargs,
    ) -> ToolResult:
        """Create an escalation request.

        Args:
            reason: Why escalation is needed.
            priority: Priority level.
            customer_email: Customer email.
            summary: Issue summary.
            interaction_id: Optional interaction log ID.

        Returns:
            ToolResult confirming escalation.
        """
        try:
            escalation_data = {
                "reason": reason,
                "priority": priority,
                "customer_email": customer_email,
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Persist to database if session available
            if self.db:
                escalation = Escalation(
                    interaction_id=interaction_id,
                    reason=reason,
                    context={
                        "priority": priority,
                        "customer_email": customer_email,
                        "summary": summary,
                    },
                    status="pending",
                )
                self.db.add(escalation)
                await self.db.flush()
                escalation_data["id"] = str(escalation.id)

            return ToolResult(
                success=True,
                data={
                    "escalated": True,
                    "escalation": escalation_data,
                    "message": (
                        "Your request has been escalated to our support team. "
                        f"A human agent will review your case with {priority} priority "
                        "and respond within 24 hours."
                    ),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to create escalation: {str(e)}",
            )
