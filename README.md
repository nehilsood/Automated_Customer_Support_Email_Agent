# Automated Customer Support Email Agent

An AI-powered customer support email agent for D2C (Direct-to-Consumer) brands. Automatically resolves customer queries by referencing FAQ, Knowledge Base, and real-time Shopify store data.

## Overview

This system uses a tool-based architecture with RAG (Retrieval Augmented Generation) to ensure responses are grounded in actual data, eliminating hallucination. Gmail serves as the input/output transport layer while the AI agent handles query understanding and response generation.

### Key Metrics

| Attribute | Target |
|-----------|--------|
| Scale | 2,500 emails/month |
| Infrastructure Cost | $0 (free tiers) |
| LLM Cost | $3-5/month |
| Response Time | < 30 seconds |
| Automation Rate | ~95% |

## Architecture

```
Email Transport (Gmail API + Pub/Sub)
           ↓
Compute Layer (Cloudflare Workers)
           ↓
Intelligence Layer (AI Agent + Tools)
           ↓
Data Layer (Supabase + Shopify API)
```

### Agent Tools

- **search_knowledge_base** - RAG for FAQ/policies/products
- **get_order** - Shopify order details
- **get_fulfillment** - Shipping and tracking info
- **get_customer_orders** - Order history by email
- **escalate_to_human** - Flag for manual review

## Tech Stack

| Component | Technology |
|-----------|------------|
| Compute | Cloudflare Workers |
| Database | Supabase PostgreSQL |
| Vector Store | Supabase pgvector |
| Email | Gmail API + Pub/Sub |
| Store Data | Shopify Admin API |
| LLMs | Gemini Flash, GPT-4o mini, Claude Sonnet |

## Project Structure

```
├── src/
│   ├── worker/          # Cloudflare Worker handlers
│   ├── agent/           # AI agent and tool definitions
│   ├── integrations/    # Gmail, Shopify, Supabase clients
│   └── utils/           # Shared utilities
├── docs/                # Additional documentation
├── scripts/             # Setup and maintenance scripts
└── tests/               # Test suites
```

## Getting Started

### Prerequisites

- Node.js 18+
- Cloudflare account
- Supabase account
- Google Cloud project (Gmail API)
- Shopify store with Admin API access
- API keys for LLM providers

### Installation

```bash
# Clone the repository
git clone https://github.com/nehilsood/Automated_Customer_Support_Email_Agent.git
cd Automated_Customer_Support_Email_Agent

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Configure your environment variables
```

### Configuration

See `.env.example` for required environment variables:

- Gmail API credentials
- Shopify API credentials
- Supabase connection details
- LLM API keys (OpenAI, Anthropic, Google)

## Development

```bash
# Run locally
npm run dev

# Run tests
npm test

# Deploy to Cloudflare
npm run deploy
```

## Documentation

See [Automated_Customer_Support_Email_Agent.md](./Automated_Customer_Support_Email_Agent.md) for the complete implementation plan including:

- Detailed architecture diagrams
- Cost breakdowns
- Implementation phases
- Anti-hallucination strategies
- Monitoring and metrics

## License

MIT
