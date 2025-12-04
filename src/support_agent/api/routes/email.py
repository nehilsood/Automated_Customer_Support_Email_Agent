"""Email processing endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.integrations.database.connection import get_db
from support_agent.services.email_processor import EmailProcessorService

router = APIRouter(prefix="/email", tags=["email"])


class EmailProcessRequest(BaseModel):
    """Request model for email processing."""

    from_email: str = Field(alias="from", description="Sender email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")
    sender_name: str | None = Field(default=None, description="Sender name")
    email_id: str | None = Field(default=None, description="Email tracking ID")

    model_config = {"populate_by_name": True}


class TokenUsage(BaseModel):
    """Token usage breakdown."""

    input: int
    output: int
    total: int


class EmailProcessResponse(BaseModel):
    """Response model for email processing."""

    success: bool
    response_text: str
    intent: str
    complexity: str
    tools_used: list[str]
    model_used: str
    tokens: TokenUsage
    response_time_ms: int
    escalated: bool
    escalation_reason: str | None
    interaction_id: str
    error: str | None = None


@router.post("/process", response_model=EmailProcessResponse)
async def process_email(
    request: EmailProcessRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailProcessResponse:
    """Process a customer support email.

    This endpoint receives a customer email, processes it through the
    AI agent, and returns a generated response.

    The agent will:
    - Classify the intent (order_status, return_request, etc.)
    - Determine complexity (simple, medium, complex)
    - Use appropriate tools (search_knowledge_base, get_order, etc.)
    - Generate a helpful response
    - Log the interaction for tracking
    """
    processor = EmailProcessorService(db)

    result = await processor.process(
        from_email=request.from_email,
        subject=request.subject,
        body=request.body,
        sender_name=request.sender_name,
        email_id=request.email_id,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error or "Email processing failed",
        )

    return EmailProcessResponse(
        success=result.success,
        response_text=result.response_text,
        intent=result.intent,
        complexity=result.complexity,
        tools_used=result.tools_used,
        model_used=result.model_used,
        tokens=TokenUsage(
            input=result.tokens_input,
            output=result.tokens_output,
            total=result.tokens_input + result.tokens_output,
        ),
        response_time_ms=result.response_time_ms,
        escalated=result.escalated,
        escalation_reason=result.escalation_reason,
        interaction_id=result.interaction_id,
    )
