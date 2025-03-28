**Roadmap de 2 días para la Base de Datos en Supabase y creación del Backend**

A continuación, se presenta un plan de trabajo de dos días para un programador que debe diseñar la base de datos en Supabase (con enfoque multi-tenant) y crear el backend principal (FastAPI u otro framework Python). Se basa en la información del proyecto B2B SaaS y la arquitectura RAG descrita.

---

## Día 1: Diseño e Implementación de la Base de Datos en Supabase

1. **Revisión de Requerimientos y Modelo de Datos**  
   - Analizar el contexto multi-cliente (cada empresa con sus propios documentos).  
   - Definir las entidades principales:  
     - **companies (empresas)**  
     - **users (usuarios)**  
     - **documents (documentos)**  
     - **document_metadata (metadatos y estados de procesamiento, OCR, etc.)**  
     - (Opcional) **embeddings** (si se planea usar pgvector para pruebas, aunque la base vectorial final sea Qdrant/Milvus).  

2. **Configuración Inicial de Supabase**  
   - Crear el proyecto en Supabase y configurar la conexión a PostgreSQL.  
   - Habilitar la autenticación nativa de Supabase (si se usará su sistema de usuarios).  
   - Crear roles y políticas de seguridad (RLS) para aislar datos por `company_id`.

3. **Diseño de Tablas y Relaciones**  
   - **Tabla `companies`**:  
     - `id` (PK), `name`, `created_at`, etc.  
   - **Tabla `users`**:  
     - `id` (PK), `email`, `password_hash` (si se gestiona internamente) o campos propios de Supabase, `company_id` (FK), `role`, etc.  
   - **Tabla `documents`**:  
     - `id` (PK), `company_id` (FK), `file_name`, `file_url` (ruta de almacenamiento), `created_at`, etc.  
   - **Tabla `document_metadata`** (opcional si no se quiere mezclar con `documents`):  
     - `id` (PK), `document_id` (FK), `ocr_status`, `chunking_status`, `updated_at`, etc.  
   - **(Opcional) Tabla `embeddings`**:  
     - `id` (PK), `document_id` (FK), `embedding_vector`, `chunk_text`, `metadata`, etc. (sólo si se decide usar pgvector en el MVP).

4. **Políticas de Seguridad (RLS) y Separación de Datos**  
   - Configurar políticas para que cada usuario sólo pueda acceder a registros donde `company_id` coincida con la empresa asociada a su JWT.  
   - Asegurarse de que Supabase emita un JWT con `company_id` y se valide en cada consulta.

5. **Migraciones y Pruebas Básicas**  
   - Generar migraciones (si se usa una herramienta tipo Prisma o SQLAlchemy) para versionar la BD.  
   - Probar la creación de empresas, usuarios y documentos desde la consola de Supabase.  
   - Verificar que el filtrado por `company_id` funciona correctamente.

**Objetivo al finalizar el Día 1**  
- Base de datos lista en Supabase con tablas creadas, relaciones definidas y seguridad multi-tenant configurada.  
- Pruebas mínimas para asegurar que se pueden insertar y consultar datos de forma aislada.

---

## Día 2: Creación del Backend (FastAPI u otro framework Python)

1. **Estructura del Proyecto Backend**  
   - Crear repositorio o carpeta para el servicio backend.  
   - Configurar entorno virtual (poetry, pipenv o requirements.txt) e instalar dependencias:  
     - `fastapi`, `uvicorn`, `requests`, `supabase-py` (si se usa el cliente oficial), etc.  
   - Preparar configuración (variables de entorno) para conectarse a la base de datos de Supabase.

2. **Endpoints de Autenticación y Usuarios**  
   - Integrar la verificación del JWT emitido por Supabase (o usar la capa de autenticación propia de Supabase y sólo validar tokens).  
   - Crear un endpoint para verificar sesión o recuperar datos de perfil (opcional, si no se usa el endpoint nativo de Supabase).

3. **Endpoints para Gestión de Empresas y Usuarios**  
   - **GET /companies**: Listar empresas (sólo si el usuario tiene rol de admin).  
   - **POST /companies**: Crear una nueva empresa (según permisos).  
   - **GET /users** y **POST /users**: Manejo de usuarios ligados a una `company_id`.

4. **Endpoints para Documentos**  
   - **POST /documents**: Subir metadatos del documento (y ruta de almacenamiento).  
     - Aquí puede integrarse la llamada a un servicio de ingesta/ocr (en MVP, quizás sólo se guarde la metadata).  
   - **GET /documents**: Listar documentos de la empresa actual.  
   - **GET /documents/{document_id}**: Detalles de un documento específico.  

5. **Integración con Servicios de Procesamiento (Ingesta, OCR, etc.)**  
   - Preparar endpoints o hooks para invocar el pipeline de ingesta (aunque sea un stub en este MVP).  
   - Definir cómo se registran los estados de OCR y chunking en la BD.

6. **Endpoints de Consulta RAG (Básico)**  
   - Definir un endpoint (p. ej., **POST /query**) que reciba la pregunta y `company_id` (desde JWT).  
   - Conectar (o dejar preparado) el proceso de:  
     1. Generar embedding de la pregunta.  
     2. Consultar la base vectorial (Qdrant/Milvus) o la tabla de embeddings en PostgreSQL (si se está haciendo un prototipo con pgvector).  
     3. Retornar el texto más relevante (chunk) y la respuesta generada por Gemini (en la fase final).  

7. **Validaciones y Pruebas de Integración**  
   - Probar el flujo de creación de usuarios, subida de documentos y consulta.  
   - Verificar que la seguridad multi-tenant funcione (un usuario no pueda ver documentos de otra empresa).

**Objetivo al finalizar el Día 2**  
- Backend funcional con endpoints para:  
  - **Autenticación** (usando tokens Supabase).  
  - **Gestión de empresas y usuarios** (multi-tenant).  
  - **Documentos** (registro, listados).  
  - **Consulta RAG** (o al menos un stub para la lógica principal).  
- Todo vinculado correctamente con la base de datos en Supabase y listo para pruebas finales.

---

### Consideraciones Finales
- **Optimización del Pipeline RAG**: Para el MVP, bastará con asegurar que se pueda hacer la ingesta y consulta de manera básica. Luego se puede escalar e integrar completamente con Qdrant o Milvus.  
- **Monitoreo y Logs**: Aunque no sea prioridad en estos 2 días, dejar bases para logging (p. ej., con `logging` de Python) y monitoreo básico.  
- **Despliegue en GKE**: Se puede posponer para después de tener la base de datos y backend funcionando localmente.  
- **Documentación**: Mantener actualizados los endpoints en un archivo OpenAPI/Swagger para que el equipo de frontend los consuma fácilmente.

Con este roadmap de 2 días se cubre la creación de la base de datos multi-tenant en Supabase y la implementación mínima del backend para soportar la funcionalidad esencial del MVP.