"""SQLAlchemy ORM models with pgvector support."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class KnowledgeBase(Base):
    """Knowledge base entries with vector embeddings for RAG."""

    __tablename__ = "knowledge_base"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    extra_data: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    embedding = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("knowledge_base_category_idx", "category"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, category={self.category}, title={self.title})>"


class InteractionLog(Base):
    """Log of all customer email interactions."""

    __tablename__ = "interaction_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    email_id: Mapped[str | None] = mapped_column(String(255))
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(50))
    complexity: Mapped[str | None] = mapped_column(String(20))
    model_used: Mapped[str | None] = mapped_column(String(50))
    tools_used: Mapped[dict[str, Any]] = mapped_column(JSONB, default=list)
    response: Mapped[str | None] = mapped_column(Text)
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationship to escalations
    escalations: Mapped[list["Escalation"]] = relationship(back_populates="interaction")

    __table_args__ = (
        Index("interaction_logs_sender_idx", "sender_email"),
        Index("interaction_logs_created_idx", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<InteractionLog(id={self.id}, sender={self.sender_email}, intent={self.intent})>"


class Escalation(Base):
    """Escalation queue for human review."""

    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    interaction_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("interaction_logs.id")
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationship to interaction
    interaction: Mapped[InteractionLog | None] = relationship(back_populates="escalations")

    __table_args__ = (Index("escalations_status_idx", "status"),)

    def __repr__(self) -> str:
        return f"<Escalation(id={self.id}, status={self.status}, reason={self.reason[:50]})>"


class ResponseCache(Base):
    """Cache for common query responses."""

    __tablename__ = "response_cache"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    query_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50))
    hit_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("response_cache_hash_idx", "query_hash"),)

    def __repr__(self) -> str:
        return f"<ResponseCache(id={self.id}, hash={self.query_hash}, hits={self.hit_count})>"
