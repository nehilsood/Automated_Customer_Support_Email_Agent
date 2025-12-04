"""Database integration package."""

from .connection import get_db, init_db
from .models import Base, Escalation, InteractionLog, KnowledgeBase, ResponseCache

__all__ = [
    "Base",
    "KnowledgeBase",
    "InteractionLog",
    "Escalation",
    "ResponseCache",
    "get_db",
    "init_db",
]
