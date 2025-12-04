# Automated Customer Support Email Agent

An AI-powered customer support email agent built with Python, FastAPI, and OpenAI. Uses RAG (Retrieval Augmented Generation) with pgvector for accurate, grounded responses.

## Features

- **Intent Classification**: Automatically classifies customer emails into 9 intent categories
- **Tiered LLM Routing**: Uses cost-effective models (gpt-4o-mini) for simple queries, advanced models (gpt-4o) for complex issues
- **RAG-Powered Responses**: Searches knowledge base using vector similarity to ensure accurate answers
- **Tool-Based Architecture**: Agent uses tools to fetch real data before responding (anti-hallucination)
- **Mock Shopify Integration**: Ready for real Shopify API with feature flag
- **Automatic Escalation**: Routes complex issues to human agents

## Architecture

```
Customer Email
       ↓
┌──────────────────┐
│ Intent Classifier │ ← gpt-4o-mini
└──────────────────┘
       ↓
┌──────────────────┐
│   LLM Router     │ ← Routes to appropriate model
└──────────────────┘
       ↓
┌──────────────────┐     ┌─────────────────────┐
│  Support Agent   │ ←→  │       Tools         │
│  (Orchestrator)  │     │ - search_kb (RAG)   │
└──────────────────┘     │ - get_order         │
       ↓                 │ - get_fulfillment   │
┌──────────────────┐     │ - get_customer_orders│
│    Response      │     │ - escalate_to_human │
└──────────────────┘     └─────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy 2.0 (async) |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Package Manager | uv |

## Project Structure

```
├── src/support_agent/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Pydantic settings
│   ├── api/routes/             # API endpoints
│   │   └── health.py           # Health check routes
│   ├── agent/                  # AI agent module
│   │   ├── core.py             # Main orchestrator
│   │   ├── classifier.py       # Intent classification
│   │   ├── router.py           # Tiered LLM routing
│   │   ├── prompts.py          # System prompts
│   │   └── tools/              # Agent tools
│   │       ├── base.py         # Tool base class
│   │       ├── knowledge_base.py
│   │       ├── shopify.py
│   │       └── escalation.py
│   ├── integrations/
│   │   ├── openai_client.py    # OpenAI API client
│   │   ├── database/           # SQLAlchemy setup
│   │   └── shopify/            # Shopify client (mock)
│   └── services/
│       ├── embedding.py        # Embedding service
│       └── rag.py              # RAG retrieval
├── data/                       # Sample data
│   ├── sample_faq.json
│   ├── sample_policies.json
│   └── sample_orders.json
├── scripts/
│   ├── seed_knowledge_base.py  # Seed KB with embeddings
│   └── test_agent.py           # Test script
├── docker-compose.yml          # PostgreSQL + pgvector
└── pyproject.toml              # Dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL)
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Automated_Customer_Support_Email_Agent

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .

# Copy environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Start Database

```bash
# Start PostgreSQL with pgvector
docker compose up -d

# Wait for database to be ready
docker compose logs -f postgres
```

### Seed Knowledge Base

```bash
# This generates embeddings and populates the KB
python scripts/seed_knowledge_base.py
```

### Run the API Server

```bash
uvicorn src.support_agent.main:app --reload
```

### Test the Agent

```bash
# Run comprehensive test suite
python scripts/test_agent.py

# Or test via API
curl http://localhost:8000/api/v1/health

# Test RAG search
curl -X POST http://localhost:8000/api/v1/health/test-rag \
  -H "Content-Type: application/json" \
  -d '{"query": "return policy"}'
```

## Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...

# Database (defaults to Docker)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/support_agent

# LLM Models
CLASSIFIER_MODEL=gpt-4o-mini
SIMPLE_MODEL=gpt-4o-mini
MEDIUM_MODEL=gpt-4o-mini
COMPLEX_MODEL=gpt-4o

# RAG Settings
RAG_TOP_K=3
RAG_SIMILARITY_THRESHOLD=0.7

# Shopify (uses mock if empty)
SHOPIFY_STORE_URL=
SHOPIFY_ACCESS_TOKEN=
USE_MOCK_SHOPIFY=true
```

## Agent Tools

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | RAG search for FAQs, policies, product info |
| `get_order` | Lookup order by order number |
| `get_fulfillment` | Get shipping/tracking info |
| `get_customer_orders` | Get all orders for a customer email |
| `escalate_to_human` | Escalate to human support agent |

## Intent Classification

The classifier identifies these intents:

- `order_status` - "Where is my order?"
- `shipping_tracking` - "Track my package"
- `return_request` - "I want to return..."
- `refund_request` - "I need a refund..."
- `product_question` - Product inquiries
- `policy_question` - Store policy questions
- `complaint` - Negative feedback
- `escalation_request` - "Speak to human"
- `general_inquiry` - Everything else

## Tiered LLM Routing

| Complexity | Model | Use Cases |
|------------|-------|-----------|
| Simple | gpt-4o-mini | Direct lookups, FAQ answers |
| Medium | gpt-4o-mini | 2-3 tool calls, moderate reasoning |
| Complex | gpt-4o | Multi-step issues, escalations |

Complaints, refund requests, and escalation requests automatically route to the complex tier.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/api/v1/health` | GET | Health check with DB status |
| `/api/v1/health/ready` | GET | Kubernetes readiness probe |
| `/api/v1/health/live` | GET | Kubernetes liveness probe |
| `/api/v1/health/test-rag` | POST | Test RAG search |

## Sample Data

The project includes mock data for testing:

- **10 FAQ entries** - Common questions and answers
- **7 Policy documents** - Return, shipping, warranty policies
- **5 Sample orders** - Mock Shopify order data

## Development Status

- [x] Phase 1: Foundation (Database, RAG, Embeddings)
- [x] Phase 2: Agent Core (Tools, Classifier, Router, Orchestrator)
- [ ] Phase 3: Email API (REST endpoints, email processing)
- [ ] Phase 4: Real Integrations (Shopify, Gmail)
- [ ] Phase 5: Production (Lambda, Supabase)

## Testing

```bash
# Run agent tests
python scripts/test_agent.py

# Test individual components
python -c "
import asyncio
from support_agent.agent.core import SupportAgent
from support_agent.integrations.database.connection import get_db_session

async def test():
    async with get_db_session() as db:
        agent = SupportAgent(db)
        response = await agent.process_email(
            subject='Order Status',
            body='Where is my order #12345?',
            sender_email='john.doe@example.com'
        )
        print(response.response_text)

asyncio.run(test())
"
```

## License

MIT
