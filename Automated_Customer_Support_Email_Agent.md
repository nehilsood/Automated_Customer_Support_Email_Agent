# # Automated Customer Support Email Agent  
## Complete Implementation Plan for D2C Brand  
  
**Document Version:** 1.0    
**Date:** December 2025    
**Scale:** Up to 2,500 emails/month    
**Estimated Monthly Cost:** $3-5  
  
---  
  
## Executive Summary  
  
This document outlines a complete system design for building an automated customer support email agent for D2C (Direct-to-Consumer) brands. The system automatically resolves customer queries by referencing FAQ, Knowledge Base, and real-time Shopify store data.  
  
The agent uses a tool-based architecture with built-in RAG (Retrieval Augmented Generation) to ensure responses are grounded in actual data, eliminating hallucination. Gmail serves as the input/output transport layer, while the AI agent focuses purely on understanding queries and generating accurate responses.  
  
### Key Metrics  
  
| Attribute | Target |  
|-----------|--------|  
| Scale | 2,500 emails/month |  
| Infrastructure Cost | $0 (free tiers) |  
| LLM Cost | $3-5/month |  
| Response Time | < 30 seconds |  
| Automation Rate | ~95% |  
| Human Escalation | ~5% |  
  
---  
  
## System Architecture  
  
### High-Level Overview  
  
The system consists of four main layers:  
  
1. **Email Transport Layer** - Gmail API for receiving and sending emails  
2. **Compute Layer** - Cloudflare Workers for orchestration  
3. **Intelligence Layer** - AI Agent with tools for decision-making  
4. **Data Layer** - Supabase (database + vectors) and Shopify API  
  
### Architecture Diagram  
  
```  
┌─────────────────────────────────────────────────────────────────────────┐  
│                          EMAIL TRANSPORT LAYER                          │  
│                                                                         │  
│   Customer Email ───► Gmail Inbox ───► Pub/Sub ───► Webhook            │  
│                                                                         │  
│   Response ◄─────────── Gmail API ◄─────────────────┘                  │  
│                                                                         │  
└─────────────────────────────────────────────────────────────────────────┘  
                                    │  
                                    ▼  
┌─────────────────────────────────────────────────────────────────────────┐  
│                           COMPUTE LAYER                                 │  
│                       (Cloudflare Workers)                              │  
│                                                                         │  
│   1. Receive webhook from Gmail Pub/Sub                                │  
│   2. Parse email content (sender, subject, body, order ID)             │  
│   3. Call AI Agent with parsed data                                    │  
│   4. Receive generated response                                        │  
│   5. Send reply via Gmail API                                          │  
│   6. Log interaction to database                                       │  
│                                                                         │  
└─────────────────────────────────────────────────────────────────────────┘  
                                    │  
                                    ▼  
┌─────────────────────────────────────────────────────────────────────────┐  
│                        INTELLIGENCE LAYER                               │  
│                           (AI Agent)                                    │  
│                                                                         │  
│   ┌─────────────────────────────────────────────────────────────────┐  │  
│   │                     AVAILABLE TOOLS                             │  │  
│   │                                                                 │  │  
│   │   • search_knowledge_base - RAG for FAQ/policies/products      │  │  
│   │   • get_order - Shopify order details                          │  │  
│   │   • get_fulfillment - Shipping and tracking info               │  │  
│   │   • get_customer_orders - Order history by email               │  │  
│   │   • escalate_to_human - Flag for manual review                 │  │  
│   │                                                                 │  │  
│   └─────────────────────────────────────────────────────────────────┘  │  
│                                                                         │  
│   ┌─────────────────────────────────────────────────────────────────┐  │  
│   │                   TIERED LLM ROUTING                            │  │  
│   │                                                                 │  │  
│   │   Classification ──► Gemini Flash (cheapest)                   │  │  
│   │         │                                                       │  │  
│   │         ├─► Template Response (40%) ──► No LLM needed          │  │  
│   │         ├─► Simple Query (40%) ──► Gemini Flash                │  │  
│   │         ├─► Medium Query (15%) ──► GPT-4o mini                 │  │  
│   │         └─► Complex Query (5%) ──► Claude Sonnet 4             │  │  
│   │                                                                 │  │  
│   └─────────────────────────────────────────────────────────────────┘  │  
│                                                                         │  
└─────────────────────────────────────────────────────────────────────────┘  
                                    │  
                                    ▼  
┌─────────────────────────────────────────────────────────────────────────┐  
│                           DATA LAYER                                    │  
│                                                                         │  
│   ┌─────────────────────────┐       ┌─────────────────────────┐        │  
│   │       SUPABASE          │       │     SHOPIFY API         │        │  
│   │                         │       │                         │        │  
│   │  • PostgreSQL database  │       │  • Orders               │        │  
│   │  • pgvector extension   │       │  • Fulfillments         │        │  
│   │  • FAQ embeddings       │       │  • Customers            │        │  
│   │  • KB embeddings        │       │  • Products             │        │  
│   │  • Interaction logs     │       │                         │        │  
│   │  • Response cache       │       │                         │        │  
│   │                         │       │                         │        │  
│   └─────────────────────────┘       └─────────────────────────┘        │  
│                                                                         │  
└─────────────────────────────────────────────────────────────────────────┘  
```  
  
### Key Design Decision: Gmail as Transport Only  
  
Gmail API is used exclusively for receiving and sending emails. It is NOT an agent tool. This design choice provides several benefits:  
  
- No Gmail MCP server required (no official one exists)  
- Simpler architecture with fewer moving parts  
- Agent focuses only on intelligence, not email operations  
- Direct API calls from Worker are more reliable  
  
---  
  
## Technology Stack  
  
### Verified Pricing (December 2025)  
  
#### Infrastructure Components  
  
| Component | Technology | Purpose | Monthly Cost |  
|-----------|------------|---------|--------------|  
| Compute | Cloudflare Workers | Webhook handling, orchestration | $0 (100K req/day free) |  
| Database | Supabase PostgreSQL | Logs, cache, customer data | $0 (500MB free) |  
| Vector Store | Supabase pgvector | FAQ/KB embeddings | $0 (included) |  
| Email Trigger | Gmail API + Pub/Sub | Receive incoming emails | $0 |  
| Email Send | Gmail API | Send reply emails | $0 |  
| Store Data | Shopify Admin API | Orders, fulfillments, customers | $0 (included with store) |  
  
#### Embedding Models  
  
| Model | Price per 1M Tokens | Dimensions | Recommendation |  
|-------|---------------------|------------|----------------|  
| OpenAI text-embedding-3-small | $0.02 | 1536 | Best cost/quality ratio ✓ |  
| OpenAI text-embedding-3-large | $0.13 | 3072 | Higher quality, overkill for support |  
| Jina Embeddings v3 | Free trial, then paid | 1024 | Good alternative |  
| Google Gemini Embedding | Free tier available | 768 | Good for GCP users |  
  
#### LLM Models (Per Million Tokens)  
  
| Model | Input Cost | Output Cost | Use Case |  
|-------|------------|-------------|----------|  
| Gemini 1.5 Flash | $0.075 | $0.30 | Classification, simple queries |  
| Gemini 2.0 Flash-Lite | $0.07 | $0.30 | Ultra cheap, high volume |  
| GPT-4o mini | $0.15 | $0.60 | Medium complexity |  
| Claude Haiku 3.5 | $0.80 | $4.00 | Better quality simple tasks |  
| Claude Haiku 4.5 | $1.00 | $5.00 | Near-frontier, fast |  
| Claude Sonnet 4 | $3.00 | $15.00 | Complex responses, complaints |  
  
---  
  
## Cost Breakdown  
  
### Infrastructure Costs (Monthly)  
  
| Service | Free Tier Limit | Your Usage | Cost |  
|---------|-----------------|------------|------|  
| Cloudflare Workers | 100,000 requests/day | ~83 requests/day | $0 |  
| Supabase Database | 500MB | ~50MB | $0 |  
| Supabase pgvector | Included | ~10MB vectors | $0 |  
| Gmail API | Unlimited | 2,500 emails | $0 |  
| Shopify API | Included with store | ~5,000 calls | $0 |  
  
**Infrastructure Total: $0/month**  
  
### Embedding Costs (Monthly)  
  
| Task | Tokens | Model | Cost |  
|------|--------|-------|------|  
| Initial FAQ/KB ingestion | ~500,000 | text-embedding-3-small | $0.01 |  
| Monthly content updates | ~100,000 | text-embedding-3-small | $0.002 |  
| Query embeddings | ~250,000 | text-embedding-3-small | $0.005 |  
  
**Embedding Total: ~$0.02/month**  
  
### LLM Costs (Monthly - 2,500 emails)  
  
| Task | Volume | Model | Cost/Query | Total |  
|------|--------|-------|------------|-------|  
| Intent Classification | 2,500 | Gemini Flash | $0.00004 | $0.10 |  
| Template Responses | 1,000 (40%) | None | $0 | $0 |  
| Simple Responses | 1,000 (40%) | Gemini Flash | $0.0004 | $0.40 |  
| Medium Responses | 375 (15%) | GPT-4o mini | $0.001 | $0.38 |  
| Complex Responses | 125 (5%) | Claude Sonnet 4 | $0.02 | $2.50 |  
  
**LLM Total: ~$3.40/month**  
  
### Total Monthly Cost  
  
| Category | Cost |  
|----------|------|  
| Infrastructure | $0 |  
| Embeddings | $0.02 |  
| LLM (per-token) | $3.40 |  
| **Total** | **~$3.50/month** |  
  
*Note: Costs scale linearly. At 5,000 emails/month, expect ~$7/month.*  
  
---  
  
## Agent Tools Specification  
  
### Tool 1: search_knowledge_base  
  
**Purpose:** Retrieve relevant information from FAQ, policies, and product documentation.  
  
| Attribute | Detail |  
|-----------|--------|  
| Input | query (string), category (optional: faq, policy, product, shipping) |  
| Output | Array of relevant text chunks with similarity scores |  
| Backend | Supabase pgvector with cosine similarity search |  
| Token Cost | ~$0.00001 per query (embedding only) |  
  
**When to Use:**  
- Customer asks about return/refund policy  
- Product-related questions  
- Shipping information queries  
- General FAQ questions  
  
### Tool 2: get_order  
  
**Purpose:** Fetch order details from Shopify.  
  
| Attribute | Detail |  
|-----------|--------|  
| Input | order_id OR customer_email |  
| Output | Order details: items, status, payment, dates, customer info |  
| Backend | Shopify Admin API |  
| Token Cost | $0 (API call only) |  
  
**When to Use:**  
- Customer asks "where is my order?"  
- Order status inquiries  
- Order modification requests  
  
### Tool 3: get_fulfillment  
  
**Purpose:** Get shipping and tracking information.  
  
| Attribute | Detail |  
|-----------|--------|  
| Input | order_id |  
| Output | Carrier, tracking number, tracking URL, delivery status, ETA |  
| Backend | Shopify Admin API (Fulfillments endpoint) |  
| Token Cost | $0 (API call only) |  
  
**When to Use:**  
- Tracking number requests  
- Delivery date questions  
- Shipping status updates  
  
### Tool 4: get_customer_orders  
  
**Purpose:** Retrieve complete order history for a customer.  
  
| Attribute | Detail |  
|-----------|--------|  
| Input | customer_email |  
| Output | List of all orders with summary info |  
| Backend | Shopify Admin API (Customer Orders endpoint) |  
| Token Cost | $0 (API call only) |  
  
**When to Use:**  
- Customer doesn't remember order number  
- Account-level inquiries  
- Return eligibility checks  
  
### Tool 5: escalate_to_human  
  
**Purpose:** Flag conversation for human review.  
  
| Attribute | Detail |  
|-----------|--------|  
| Input | reason (string), context (object) |  
| Output | Confirmation, ticket ID |  
| Backend | Supabase (creates escalation record), optional Slack notification |  
| Token Cost | $0 |  
  
**When to Use:**  
- Complaints or angry customers  
- Refund requests above threshold  
- Complex issues agent cannot resolve  
- RAG confidence score below threshold  
  
---  
  
## Query Routing Logic  
  
### Intent Classification Categories  
  
| Intent | Example Queries | Routing |  
|--------|-----------------|---------|  
| ORDER_STATUS | "Where is my order?", "Order #12345 status" | Template + Shopify |  
| TRACKING | "Track my package", "When will it arrive?" | Template + Shopify |  
| RETURN_POLICY | "How do I return?", "Refund policy" | RAG → Simple LLM |  
| PRODUCT_QUESTION | "What size should I get?", "Is this waterproof?" | RAG → Simple LLM |  
| SHIPPING_INFO | "How long does shipping take?", "Do you ship to Canada?" | RAG → Simple LLM |  
| ORDER_CHANGE | "Cancel my order", "Change shipping address" | Medium LLM + Escalate |  
| COMPLAINT | "This is unacceptable", "I want a refund" | Complex LLM + Escalate |  
| GENERAL | "Hello", "Thanks" | Template |  
  
### Routing Decision Tree  
  
```  
┌─────────────────────────────────────────────────────────────────┐  
│                    INCOMING EMAIL                               │  
└─────────────────────────────────────────────────────────────────┘  
                              │  
                              ▼  
┌─────────────────────────────────────────────────────────────────┐  
│              STEP 1: INTENT CLASSIFICATION                      │  
│                    (Gemini Flash)                               │  
│                                                                 │  
│   Extract: intent_type, complexity_score, entities (order_id)  │  
│                                                                 │  
└─────────────────────────────────────────────────────────────────┘  
                              │  
            ┌─────────────────┼─────────────────┐  
            ▼                 ▼                 ▼  
     ┌────────────┐    ┌────────────┐    ┌────────────┐  
     │  ORDER     │    │   INFO     │    │  ISSUE     │  
     │  QUERIES   │    │  QUERIES   │    │  QUERIES   │  
     │            │    │            │    │            │  
     │ • Status   │    │ • FAQ      │    │ • Complaint│  
     │ • Tracking │    │ • Policy   │    │ • Refund   │  
     │ • History  │    │ • Product  │    │ • Problem  │  
     └─────┬──────┘    └─────┬──────┘    └─────┬──────┘  
           │                 │                 │  
           ▼                 ▼                 ▼  
     ┌────────────┐    ┌────────────┐    ┌────────────┐  
     │  TEMPLATE  │    │  RAG +     │    │  RAG +     │  
     │    PATH    │    │ SIMPLE LLM │    │COMPLEX LLM │  
     │            │    │            │    │            │  
     │ Shopify    │    │ Search KB  │    │ Full       │  
     │ Data +     │    │ then       │    │ context +  │  
     │ Template   │    │ Generate   │    │ Escalate   │  
     │            │    │            │    │            │  
     │ Cost: $0   │    │ Cost: low  │    │ Cost: high │  
     └────────────┘    └────────────┘    └────────────┘  
```  
  
---  
  
## Anti-Hallucination Strategy  
  
### Core Principles  
  
The agent must NEVER fabricate information. All responses must be grounded in tool outputs.  
  
### Mandatory Rules  
  
1. **Always Use Tools First**  
   - Never respond to order queries without calling Shopify tools  
   - Never answer policy questions without searching knowledge base  
   - If unsure, search first, then respond  
  
2. **Ground Responses in Tool Outputs**  
   - Only include information explicitly returned by tools  
   - Quote tracking numbers, dates, and prices exactly as returned  
   - If tool returns empty, acknowledge: "I couldn't find..."  
  
3. **Confidence Thresholds**  
   - RAG similarity score < 0.7 → escalate to human  
   - Multiple failed tool calls → escalate to human  
   - Ambiguous query → ask clarifying question  
  
4. **Structured Data Handling**  
   - Order information: ONLY from Shopify tools  
   - Policy information: ONLY from RAG tool  
   - Tracking numbers: ONLY from fulfillment tool  
   - Prices: ONLY from order or product tools  
  
### System Prompt Requirements  
  
The agent system prompt must include:  
  
- Explicit instruction to use tools before responding  
- List of information types that must come from tools  
- Instructions for handling empty tool responses  
- Escalation triggers and thresholds  
- Brand voice and tone guidelines  
  
---  
  
## Data Requirements  
  
### Knowledge Base Content  
  
| Content Type | Description | Update Frequency |  
|--------------|-------------|------------------|  
| FAQ | Common customer questions and answers | Monthly |  
| Return Policy | Return windows, conditions, process | As needed |  
| Refund Policy | Refund timelines, methods, conditions | As needed |  
| Shipping Policy | Carriers, timeframes, costs, regions | As needed |  
| Product Info | Descriptions, sizing, care instructions | Per product launch |  
| Brand Guidelines | Tone, prohibited phrases, escalation rules | Quarterly |  
  
### Database Schema Requirements  
  
**Tables Needed:**  
  
1. **knowledge_base** - FAQ and policy content with embeddings  
2. **interaction_logs** - All customer interactions for analytics  
3. **response_cache** - Cached responses for common queries  
4. **escalations** - Human review queue  
5. **templates** - Response templates for common scenarios  
  
### Shopify Data Access  
  
| Endpoint | Data Retrieved | Permission Scope |  
|----------|----------------|------------------|  
| GET /orders/{id} | Order details | read_orders |  
| GET /orders/{id}/fulfillments | Shipping info | read_orders |  
| GET /customers/search | Customer lookup | read_customers |  
| GET /products/{id} | Product details | read_products |  
  
---  
  
## Implementation Phases  
  
### Phase 1: Foundation (Week 1)  
  
**Objectives:**  
- Set up infrastructure accounts  
- Create database schema  
- Ingest initial knowledge base content  
  
**Tasks:**  
- Create Supabase project with pgvector extension  
- Design and create database tables  
- Set up Cloudflare Workers account  
- Collect and format FAQ/KB content  
- Generate embeddings for knowledge base  
- Test vector search quality  
  
**Deliverables:**  
- Working database with pgvector  
- Knowledge base populated and searchable  
- Basic Worker skeleton deployed  
  
### Phase 2: Shopify Integration (Week 2)  
  
**Objectives:**  
- Connect to Shopify Admin API  
- Build order lookup functionality  
- Create response templates  
  
**Tasks:**  
- Create Shopify private app with required scopes  
- Implement order retrieval by ID and email  
- Implement fulfillment/tracking retrieval  
- Design response templates for order queries  
- Test with sample orders  
  
**Deliverables:**  
- Working Shopify API integration  
- Order status templates  
- Tracking info templates  
  
### Phase 3: AI Agent Core (Week 3)  
  
**Objectives:**  
- Build agent with tool definitions  
- Implement intent classification  
- Set up tiered LLM routing  
  
**Tasks:**  
- Define tool schemas for agent  
- Create system prompt with anti-hallucination rules  
- Implement intent classifier  
- Build routing logic for LLM tiers  
- Connect RAG tool to knowledge base  
- Test agent responses  
  
**Deliverables:**  
- Functional AI agent with tools  
- Intent classification working  
- Tiered routing implemented  
  
### Phase 4: Email Integration (Week 4)  
  
**Objectives:**  
- Set up Gmail API connection  
- Implement Pub/Sub webhook  
- Build email sending functionality  
  
**Tasks:**  
- Create Google Cloud project  
- Enable Gmail API  
- Set up Pub/Sub topic and subscription  
- Implement webhook handler in Worker  
- Build email parsing logic  
- Implement reply functionality  
- Set up logging  
  
**Deliverables:**  
- Gmail trigger working  
- Email parsing complete  
- Reply sending functional  
  
### Phase 5: Testing and Optimization (Week 5)  
  
**Objectives:**  
- Test with real email scenarios  
- Implement caching  
- Add monitoring  
  
**Tasks:**  
- Create test email dataset  
- Run end-to-end tests  
- Implement response caching  
- Add confidence scoring  
- Build escalation workflow  
- Set up monitoring dashboard  
- Tune prompts for quality  
  
**Deliverables:**  
- Test results documented  
- Caching implemented  
- Monitoring dashboard live  
  
### Phase 6: Launch (Week 6)  
  
**Objectives:**  
- Shadow mode testing  
- Gradual rollout  
- Documentation  
  
**Tasks:**  
- Run shadow mode (generate but don't send)  
- Review shadow mode responses  
- 10% traffic rollout  
- Monitor and fix issues  
- 50% traffic rollout  
- 100% traffic rollout  
- Create operations documentation  
  
**Deliverables:**  
- Production system live  
- Operations runbook  
- Handoff documentation  
  
---  
  
## Monitoring and Metrics  
  
### Key Performance Indicators  
  
| Metric | Target | Measurement |  
|--------|--------|-------------|  
| Response Time | < 30 seconds | Time from email receipt to reply sent |  
| Resolution Rate | > 90% | Queries resolved without human intervention |  
| Escalation Rate | < 10% | Percentage sent to human review |  
| Customer Satisfaction | > 4.0/5.0 | Post-interaction surveys |  
| Cost per Email | < $0.002 | Total monthly cost / emails processed |  
  
### Monitoring Dashboard Metrics  
  
**Volume Metrics:**  
- Emails processed per hour/day/week  
- Peak traffic times  
- Query type distribution  
  
**Quality Metrics:**  
- Intent classification accuracy  
- RAG retrieval relevance scores  
- Response confidence scores  
- Customer reply rate (indicates unresolved)  
  
**Cost Metrics:**  
- LLM tokens used per model  
- Cost per query by type  
- Daily/weekly/monthly spend  
  
**Error Metrics:**  
- API failures (Gmail, Shopify)  
- LLM errors  
- Tool execution failures  
  
---  
  
## Risk Mitigation  
  
### Identified Risks and Mitigations  
  
| Risk | Impact | Likelihood | Mitigation |  
|------|--------|------------|------------|  
| Hallucinated order info | High | Medium | Mandatory tool use, never generate order data |  
| Angry customer mishandled | High | Low | Sentiment detection, auto-escalate negative tone |  
| API rate limits | Medium | Low | Caching, exponential backoff |  
| Cost spike | Medium | Low | Daily budget alerts, max token limits |  
| Email delivery failure | Medium | Low | Retry queue, failure notifications |  
| Incorrect policy info | Medium | Medium | Regular KB updates, source attribution |  
  
### Fallback Strategies  
  
1. **LLM API Down:** Queue emails for retry, send acknowledgment  
2. **Shopify API Down:** Apologize, provide manual tracking link  
3. **High Volume Spike:** Increase response time, prioritize by sentiment  
4. **Budget Exceeded:** Switch to cheaper model tier, queue non-urgent  
  
---  
  
## Future Enhancements  
  
### Phase 2 Features (Post-Launch)  
  
- Multi-language support  
- Voice/phone integration  
- Proactive order updates  
- Customer sentiment tracking over time  
- A/B testing for response variants  
  
### Scaling Considerations  
  
| Scale | Adjustments Needed |  
|-------|-------------------|  
| 5,000 emails/month | Same stack, ~$7/month |  
| 10,000 emails/month | Consider Supabase Pro ($25/month) |  
| 25,000 emails/month | Move to AWS Lambda + RDS |  
| 50,000+ emails/month | Self-hosted embedding model, dedicated infrastructure |  
  
---  
  
## Appendix A: Cloudflare Workers Free Tier Limits  
  
| Resource | Free Tier Limit |  
|----------|-----------------|  
| Requests | 100,000 per day |  
| CPU Time | 10ms per request |  
| Memory | 128MB |  
| Script Size | 1MB |  
| Workers | 100 per account |  
  
*Limits reset daily at UTC midnight*  
  
---  
  
## Appendix B: Supabase Free Tier Limits  
  
| Resource | Free Tier Limit |  
|----------|-----------------|  
| Database Size | 500MB |  
| Storage | 1GB |  
| Bandwidth | 2GB |  
| Edge Functions | 500,000 invocations |  
| Realtime | 200 concurrent connections |  
  
---  
  
## Appendix C: MCP Server Options  
  
### Shopify Integration  
  
**Official Shopify Dev MCP:** Documentation access only (not store operations)  
  
**Recommended:** Community shopify-mcp by GeLi2001  
- NPM Package: shopify-mcp  
- Provides: get_order, get_customer, get_fulfillment, get_product  
- GitHub: github.com/GeLi2001/shopify-mcp  
  
**Alternative:** Direct Shopify Admin API integration (recommended for production)  
  
### Gmail Integration  
  
**No official Gmail MCP exists.**  
  
**Options:**  
- Direct Gmail API integration (recommended)  
- Community mcp-gsuite (Gmail + Calendar)  
- Composio Gmail MCP (managed service)  
  
**Recommendation:** Use direct Gmail API calls from Worker - simpler and more reliable.  
  
---  
  
## Document Control  
  
| Version | Date | Author | Changes |  
|---------|------|--------|---------|  
| 1.0 | December 2025 | - | Initial release |  
  
---  
  
*End of Document*  
