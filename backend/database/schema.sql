-- Project Database Schema
-- This file provides context for the AI Codebase Assistant.
-- Add your actual database tables and relationships here.

-- Example: Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    content_type TEXT,
    size_bytes BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Example: Vector Embeddings Table (if using a DB-based vector store)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) -- For pgvector or similar
);
