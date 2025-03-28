CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(document_id, chunk_index)
);

-- Habilitar RLS
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Política para ver chunks de documentos de su compañía
CREATE POLICY "Users can view their company document chunks" ON document_chunks
    FOR SELECT
    USING (
        document_id IN (
            SELECT id FROM documents 
            WHERE company_id = (SELECT company_id FROM users WHERE id = auth.uid())
        )
    );

-- Política para crear/actualizar chunks (solo sistema)
CREATE POLICY "Service role can manage chunks" ON document_chunks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);