"""Admin endpoints for managing interactions and escalations."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.integrations.database.connection import get_db
from support_agent.integrations.database.models import Escalation, InteractionLog

router = APIRouter(prefix="/admin", tags=["admin"])


# --- Interaction Models ---


class InteractionSummary(BaseModel):
    """Summary of an interaction."""

    id: str
    email_id: str | None
    sender_email: str
    subject: str | None
    intent: str | None
    complexity: str | None
    model_used: str | None
    tools_used: list[str]
    tokens_input: int | None
    tokens_output: int | None
    response_time_ms: int | None
    created_at: datetime


class InteractionDetail(InteractionSummary):
    """Detailed view of an interaction."""

    body: str | None
    response: str | None


class InteractionListResponse(BaseModel):
    """Response for interaction list."""

    interactions: list[InteractionSummary]
    total: int
    limit: int
    offset: int


# --- Escalation Models ---


class EscalationSummary(BaseModel):
    """Summary of an escalation."""

    id: str
    interaction_id: str | None
    reason: str
    status: str
    assigned_to: str | None
    created_at: datetime
    resolved_at: datetime | None


class EscalationDetail(EscalationSummary):
    """Detailed view of an escalation."""

    context: dict
    resolution_notes: str | None
    interaction: InteractionSummary | None = None


class EscalationListResponse(BaseModel):
    """Response for escalation list."""

    escalations: list[EscalationSummary]
    total: int
    limit: int
    offset: int


class EscalationUpdateRequest(BaseModel):
    """Request to update an escalation."""

    status: str | None = None
    assigned_to: str | None = None
    resolution_notes: str | None = None


# --- Interaction Endpoints ---


@router.get("/interactions", response_model=InteractionListResponse)
async def list_interactions(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sender_email: str | None = Query(default=None),
    intent: str | None = Query(default=None),
) -> InteractionListResponse:
    """List recent interactions with optional filtering.

    Query Parameters:
    - limit: Maximum number of results (1-100, default 20)
    - offset: Number of records to skip (default 0)
    - sender_email: Filter by sender email
    - intent: Filter by intent type
    """
    # Build query
    query = select(InteractionLog).order_by(InteractionLog.created_at.desc())

    if sender_email:
        query = query.where(InteractionLog.sender_email == sender_email)
    if intent:
        query = query.where(InteractionLog.intent == intent)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    interactions = result.scalars().all()

    return InteractionListResponse(
        interactions=[
            InteractionSummary(
                id=i.id,
                email_id=i.email_id,
                sender_email=i.sender_email,
                subject=i.subject,
                intent=i.intent,
                complexity=i.complexity,
                model_used=i.model_used,
                tools_used=i.tools_used if isinstance(i.tools_used, list) else [],
                tokens_input=i.tokens_input,
                tokens_output=i.tokens_output,
                response_time_ms=i.response_time_ms,
                created_at=i.created_at,
            )
            for i in interactions
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/interactions/{interaction_id}", response_model=InteractionDetail)
async def get_interaction(
    interaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> InteractionDetail:
    """Get detailed information about a specific interaction."""
    query = select(InteractionLog).where(InteractionLog.id == interaction_id)
    result = await db.execute(query)
    interaction = result.scalar_one_or_none()

    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    return InteractionDetail(
        id=interaction.id,
        email_id=interaction.email_id,
        sender_email=interaction.sender_email,
        subject=interaction.subject,
        body=interaction.body,
        intent=interaction.intent,
        complexity=interaction.complexity,
        model_used=interaction.model_used,
        tools_used=interaction.tools_used if isinstance(interaction.tools_used, list) else [],
        response=interaction.response,
        tokens_input=interaction.tokens_input,
        tokens_output=interaction.tokens_output,
        response_time_ms=interaction.response_time_ms,
        created_at=interaction.created_at,
    )


# --- Escalation Endpoints ---


@router.get("/escalations", response_model=EscalationListResponse)
async def list_escalations(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
) -> EscalationListResponse:
    """List escalations with optional status filter.

    Query Parameters:
    - limit: Maximum number of results (1-100, default 20)
    - offset: Number of records to skip (default 0)
    - status: Filter by status (pending, assigned, resolved)
    """
    # Build query
    query = select(Escalation).order_by(Escalation.created_at.desc())

    if status:
        query = query.where(Escalation.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    escalations = result.scalars().all()

    return EscalationListResponse(
        escalations=[
            EscalationSummary(
                id=e.id,
                interaction_id=e.interaction_id,
                reason=e.reason,
                status=e.status,
                assigned_to=e.assigned_to,
                created_at=e.created_at,
                resolved_at=e.resolved_at,
            )
            for e in escalations
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/escalations/{escalation_id}", response_model=EscalationDetail)
async def get_escalation(
    escalation_id: str,
    db: AsyncSession = Depends(get_db),
) -> EscalationDetail:
    """Get detailed information about a specific escalation."""
    query = select(Escalation).where(Escalation.id == escalation_id)
    result = await db.execute(query)
    escalation = result.scalar_one_or_none()

    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    # Get associated interaction if exists
    interaction_summary = None
    if escalation.interaction_id:
        int_query = select(InteractionLog).where(InteractionLog.id == escalation.interaction_id)
        int_result = await db.execute(int_query)
        interaction = int_result.scalar_one_or_none()
        if interaction:
            interaction_summary = InteractionSummary(
                id=interaction.id,
                email_id=interaction.email_id,
                sender_email=interaction.sender_email,
                subject=interaction.subject,
                intent=interaction.intent,
                complexity=interaction.complexity,
                model_used=interaction.model_used,
                tools_used=interaction.tools_used if isinstance(interaction.tools_used, list) else [],
                tokens_input=interaction.tokens_input,
                tokens_output=interaction.tokens_output,
                response_time_ms=interaction.response_time_ms,
                created_at=interaction.created_at,
            )

    return EscalationDetail(
        id=escalation.id,
        interaction_id=escalation.interaction_id,
        reason=escalation.reason,
        status=escalation.status,
        assigned_to=escalation.assigned_to,
        context=escalation.context,
        resolution_notes=escalation.resolution_notes,
        created_at=escalation.created_at,
        resolved_at=escalation.resolved_at,
        interaction=interaction_summary,
    )


@router.patch("/escalations/{escalation_id}", response_model=EscalationDetail)
async def update_escalation(
    escalation_id: str,
    update: EscalationUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> EscalationDetail:
    """Update an escalation status or assignment.

    Body:
    - status: New status (pending, assigned, resolved)
    - assigned_to: Agent email/name to assign to
    - resolution_notes: Notes about the resolution
    """
    query = select(Escalation).where(Escalation.id == escalation_id)
    result = await db.execute(query)
    escalation = result.scalar_one_or_none()

    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    # Update fields
    if update.status is not None:
        escalation.status = update.status
        if update.status == "resolved":
            escalation.resolved_at = datetime.utcnow()

    if update.assigned_to is not None:
        escalation.assigned_to = update.assigned_to
        if escalation.status == "pending":
            escalation.status = "assigned"

    if update.resolution_notes is not None:
        escalation.resolution_notes = update.resolution_notes

    await db.commit()
    await db.refresh(escalation)

    # Get associated interaction
    interaction_summary = None
    if escalation.interaction_id:
        int_query = select(InteractionLog).where(InteractionLog.id == escalation.interaction_id)
        int_result = await db.execute(int_query)
        interaction = int_result.scalar_one_or_none()
        if interaction:
            interaction_summary = InteractionSummary(
                id=interaction.id,
                email_id=interaction.email_id,
                sender_email=interaction.sender_email,
                subject=interaction.subject,
                intent=interaction.intent,
                complexity=interaction.complexity,
                model_used=interaction.model_used,
                tools_used=interaction.tools_used if isinstance(interaction.tools_used, list) else [],
                tokens_input=interaction.tokens_input,
                tokens_output=interaction.tokens_output,
                response_time_ms=interaction.response_time_ms,
                created_at=interaction.created_at,
            )

    return EscalationDetail(
        id=escalation.id,
        interaction_id=escalation.interaction_id,
        reason=escalation.reason,
        status=escalation.status,
        assigned_to=escalation.assigned_to,
        context=escalation.context,
        resolution_notes=escalation.resolution_notes,
        created_at=escalation.created_at,
        resolved_at=escalation.resolved_at,
        interaction=interaction_summary,
    )
