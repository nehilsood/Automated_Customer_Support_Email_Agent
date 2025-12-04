#!/usr/bin/env python3
"""Seed the knowledge base with FAQ and policy content."""

import asyncio
import json
from pathlib import Path

from support_agent.config import get_settings
from support_agent.integrations.database.connection import get_db_session
from support_agent.integrations.database.models import KnowledgeBase
from support_agent.services.embedding import EmbeddingService


async def load_json_file(file_path: Path) -> list[dict]:
    """Load JSON data from file."""
    with open(file_path, "r") as f:
        return json.load(f)


async def seed_knowledge_base():
    """Seed knowledge base with sample data and generate embeddings."""
    settings = get_settings()
    embedding_service = EmbeddingService()

    # Define data files
    data_dir = Path(__file__).parent.parent / "data"
    data_files = [
        data_dir / "sample_faq.json",
        data_dir / "sample_policies.json",
    ]

    print("Starting knowledge base seeding...")
    print(f"Using embedding model: {settings.embedding_model}")

    total_entries = 0

    async with get_db_session() as db:
        for file_path in data_files:
            if not file_path.exists():
                print(f"Warning: {file_path} not found, skipping...")
                continue

            print(f"\nProcessing {file_path.name}...")
            entries = await load_json_file(file_path)

            for entry in entries:
                # Check if entry already exists (by title and category)
                from sqlalchemy import select

                existing = await db.execute(
                    select(KnowledgeBase).where(
                        KnowledgeBase.title == entry.get("title"),
                        KnowledgeBase.category == entry["category"],
                    )
                )
                if existing.scalar_one_or_none():
                    print(f"  Skipping existing: {entry.get('title', 'Untitled')}")
                    continue

                # Generate embedding for the content
                print(f"  Generating embedding for: {entry.get('title', 'Untitled')}")
                embedding = await embedding_service.embed_text(entry["content"])

                # Create knowledge base entry
                kb_entry = KnowledgeBase(
                    content=entry["content"],
                    category=entry["category"],
                    title=entry.get("title"),
                    extra_data=entry.get("metadata", {}),
                    embedding=embedding,
                )

                db.add(kb_entry)
                total_entries += 1

        await db.commit()

    print(f"\nSeeding complete! Added {total_entries} entries to knowledge base.")


def main():
    """Entry point for the script."""
    asyncio.run(seed_knowledge_base())


if __name__ == "__main__":
    main()
