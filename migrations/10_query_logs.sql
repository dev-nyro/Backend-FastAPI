CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    query TEXT NOT NULL,
    response TEXT,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Habilitar RLS
ALTER TABLE query_logs ENABLE ROW LEVEL SECURITY;

-- Política para ver logs de su propia compañía
CREATE POLICY "Users can view their company query logs" ON query_logs
    FOR SELECT
    USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Política para crear logs (usuarios autenticados)
CREATE POLICY "Users can create query logs" ON query_logs
    FOR INSERT
    WITH CHECK (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Política para servicio
CREATE POLICY "Service role can manage all logs" ON query_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);