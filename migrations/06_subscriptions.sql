-- Drop existing table if needed
DROP TABLE IF EXISTS subscriptions CASCADE;

-- Create subscriptions table according to schema
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    plan_type TEXT NOT NULL CHECK (plan_type IN ('free', 'pro', 'enterprise')),
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    max_documents INTEGER NOT NULL,
    max_queries INTEGER NOT NULL
);

-- Habilitar RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Política para ver suscripciones de su propia compañía
CREATE POLICY "Users can view their company subscriptions" ON subscriptions
    FOR SELECT
    USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Política para crear/actualizar suscripciones (solo admin)
CREATE POLICY "Admins can manage subscriptions" ON subscriptions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND role = 'admin'
        )
    );