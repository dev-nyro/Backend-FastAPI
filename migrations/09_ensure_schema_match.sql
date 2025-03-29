-- Ensure DOCUMENTS table matches schema exactly
ALTER TABLE documents
    ALTER COLUMN metadata SET DEFAULT '{}'::jsonb,
    ALTER COLUMN chunk_count SET DEFAULT 0,
    ALTER COLUMN status SET DEFAULT 'uploaded';

-- Ensure DOCUMENT_CHUNKS table matches schema exactly
ALTER TABLE document_chunks
    ALTER COLUMN metadata SET DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS embedding_vector float[] NULL;

-- Add missing constraints
ALTER TABLE users 
    ALTER COLUMN role SET NOT NULL,
    ALTER COLUMN full_name SET NOT NULL;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_company_id ON subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_id ON document_chunks(embedding_id);
