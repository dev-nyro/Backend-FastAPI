-- Insertar datos en COMPANIES
INSERT INTO companies (id, name, email, created_at, updated_at, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Acme Corp', 'contact@acme.com', NOW(), NOW(), TRUE),
('550e8400-e29b-41d4-a716-446655440001', 'TechBit', 'hello@techbit.com', NOW(), NOW(), TRUE);

-- Insertar datos en USERS
INSERT INTO users (id, company_id, email, full_name, role, created_at, last_login, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440000', 'alice@acme.com', 'Alice Smith', 'admin', NOW(), NULL, TRUE),
('550e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440000', 'bob@acme.com', 'Bob Johnson', 'user', NOW(), NULL, TRUE),
('550e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440001', 'carol@techbit.com', 'Carol Lee', 'admin', NOW(), NULL, TRUE);

-- Insertar datos en SUBSCRIPTIONS
INSERT INTO subscriptions (id, company_id, plan_type, start_date, end_date, max_documents, max_queries) VALUES
('550e8400-e29b-41d4-a716-446655440020', '550e8400-e29b-41d4-a716-446655440000', 'pro', NOW(), NOW() + INTERVAL '1 year', 1000, 5000),
('550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001', 'free', NOW(), NOW() + INTERVAL '1 month', 50, 200);