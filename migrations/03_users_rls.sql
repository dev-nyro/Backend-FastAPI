-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy for inserting users
CREATE POLICY "Enable insert for service role" ON users
  FOR INSERT TO service_role
  WITH CHECK (true);

-- Policy for viewing users (users can see others in their company)
CREATE POLICY "Users can view company users" ON users
  FOR SELECT TO authenticated
  USING (company_id = auth.jwt() ->> 'company_id'::text);

-- Policy for service role to do everything (needed for tests)
CREATE POLICY "Enable all for service_role" ON users
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);
