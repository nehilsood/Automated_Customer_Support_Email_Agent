"""Email processing service."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.agent.core import AgentResponse, SupportAgent
from support_agent.integrations.database.models import InteractionLog
from support_agent.integrations.email.parser import EmailParser, ParsedEmail


@dataclass
class ProcessedEmailResponse:
    """Response from email processing."""

    success: bool
    response_text: str
    intent: str
    complexity: str
    tools_used: list[str]
    model_used: str
    tokens_input: int
    tokens_output: int
    response_time_ms: int
    escalated: bool
    escalation_reason: str | None
    interaction_id: str
    error: str | None = None


class EmailProcessorService:
    """Service for processing customer support emails."""

    def __init__(self, db: AsyncSession):
        """Initialize email processor.

        Args:
            db: Database session.
        """
        self.db = db
        self.parser = EmailParser()
        self.agent = SupportAgent(db)

    async def process(
        self,
        from_email: str,
        subject: str,
        body: str,
        sender_name: str | None = None,
        email_id: str | None = None,
    ) -> ProcessedEmailResponse:
        """Process a customer email and generate response.

        Args:
            from_email: Sender email address.
            subject: Email subject.
            body: Email body.
            sender_name: Optional sender name.
            email_id: Optional email tracking ID.

        Returns:
            ProcessedEmailResponse with result and metadata.
        """
        try:
            # Parse email
            parsed = self.parser.parse(
                from_email=from_email,
                subject=subject,
                body=body,
                sender_name=sender_name,
                email_id=email_id,
            )

            # Process with agent
            agent_response = await self.agent.process_email(
                subject=parsed.subject,
                body=parsed.body,
                sender_email=parsed.sender_email,
                sender_name=parsed.sender_name,
            )

            # Log interaction
            interaction_id = await self._log_interaction(
                parsed_email=parsed,
                agent_response=agent_response,
            )

            return ProcessedEmailResponse(
                success=True,
                response_text=agent_response.response_text,
                intent=agent_response.classification.intent.value,
                complexity=agent_response.classification.complexity.value,
                tools_used=agent_response.tools_used,
                model_used=agent_response.model_used,
                tokens_input=agent_response.tokens_input,
                tokens_output=agent_response.tokens_output,
                response_time_ms=agent_response.response_time_ms,
                escalated=agent_response.escalated,
                escalation_reason=agent_response.escalation_reason,
                interaction_id=interaction_id,
            )

        except ValueError as e:
            # Validation error (e.g., invalid email)
            return ProcessedEmailResponse(
                success=False,
                response_text="",
                intent="unknown",
                complexity="unknown",
                tools_used=[],
                model_used="none",
                tokens_input=0,
                tokens_output=0,
                response_time_ms=0,
                escalated=False,
                escalation_reason=None,
                interaction_id="",
                error=str(e),
            )

        except Exception as e:
            # Unexpected error
            return ProcessedEmailResponse(
                success=False,
                response_text="",
                intent="unknown",
                complexity="unknown",
                tools_used=[],
                model_used="none",
                tokens_input=0,
                tokens_output=0,
                response_time_ms=0,
                escalated=False,
                escalation_reason=None,
                interaction_id="",
                error=f"Processing error: {str(e)}",
            )

    async def _log_interaction(
        self,
        parsed_email: ParsedEmail,
        agent_response: AgentResponse,
    ) -> str:
        """Log interaction to database.

        Args:
            parsed_email: Parsed email data.
            agent_response: Agent response data.

        Returns:
            Interaction ID.
        """
        interaction = InteractionLog(
            email_id=parsed_email.email_id,
            sender_email=parsed_email.sender_email,
            subject=parsed_email.subject,
            body=parsed_email.body,
            intent=agent_response.classification.intent.value,
            complexity=agent_response.classification.complexity.value,
            model_used=agent_response.model_used,
            tools_used=agent_response.tools_used,
            response=agent_response.response_text,
            tokens_input=agent_response.tokens_input,
            tokens_output=agent_response.tokens_output,
            response_time_ms=agent_response.response_time_ms,
        )

        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)

        return interaction.id
