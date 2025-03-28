CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    chunk_count INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'uploaded'
);

-- Políticas RLS para documentos
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy para ver documentos solo de su propia compañía
CREATE POLICY "Users can view their company documents" ON documents
    FOR SELECT
    USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Policy para insertar documentos
CREATE POLICY "Users can insert documents for their company" ON documents
    FOR INSERT
    WITH CHECK (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Policy para actualizar documentos
CREATE POLICY "Users can update their company documents" ON documents
    FOR UPDATE
    USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Policy para eliminar documentos
CREATE POLICY "Users can delete their company documents" ON documents
    FOR DELETE
    USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));