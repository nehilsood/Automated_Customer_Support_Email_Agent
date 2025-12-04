-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base table with vector embeddings
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx
ON knowledge_base USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS knowledge_base_category_idx ON knowledge_base(category);

-- Interaction logs for analytics
CREATE TABLE IF NOT EXISTS interaction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    intent VARCHAR(50),
    complexity VARCHAR(20),
    model_used VARCHAR(50),
    tools_used JSONB DEFAULT '[]',
    response TEXT,
    tokens_input INTEGER,
    tokens_output INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying by sender
CREATE INDEX IF NOT EXISTS interaction_logs_sender_idx ON interaction_logs(sender_email);
CREATE INDEX IF NOT EXISTS interaction_logs_created_idx ON interaction_logs(created_at);

-- Escalations queue for human review
CREATE TABLE IF NOT EXISTS escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id UUID REFERENCES interaction_logs(id),
    reason TEXT NOT NULL,
    context JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(255),
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for filtering by status
CREATE INDEX IF NOT EXISTS escalations_status_idx ON escalations(status);

-- Response cache for common queries
CREATE TABLE IF NOT EXISTS response_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    response TEXT NOT NULL,
    intent VARCHAR(50),
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Index for cache lookups
CREATE INDEX IF NOT EXISTS response_cache_hash_idx ON response_cache(query_hash);
