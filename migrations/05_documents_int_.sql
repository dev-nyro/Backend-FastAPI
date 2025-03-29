-- Políticas para el bucket documents
CREATE POLICY "Authenticated users can upload files"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'documents' AND
    (auth.role() = 'authenticated')
);

-- Solo permitir acceso a archivos de la misma empresa
CREATE POLICY "Users can view files from their company"
ON storage.objects FOR SELECT TO authenticated
USING (
    bucket_id = 'documents' AND
    (
        -- Obtiene company_id del path del archivo (format: companies/{company_id}/*)
        (SPLIT_PART(name, '/', 2))::uuid IN (
            SELECT company_id 
            FROM users 
            WHERE id = auth.uid()
        )
    )
);

-- Permitir actualización solo a archivos de su empresa
CREATE POLICY "Users can update their company files"
ON storage.objects FOR UPDATE TO authenticated
USING (
    bucket_id = 'documents' AND
    (
        (SPLIT_PART(name, '/', 2))::uuid IN (
            SELECT company_id 
            FROM users 
            WHERE id = auth.uid()
        )
    )
);

-- Permitir eliminación solo a archivos de su empresa
CREATE POLICY "Users can delete their company files"
ON storage.objects FOR DELETE TO authenticated
USING (
    bucket_id = 'documents' AND
    (
        (SPLIT_PART(name, '/', 2))::uuid IN (
            SELECT company_id 
            FROM users 
            WHERE id = auth.uid()
        )
    )
);