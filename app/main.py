from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
# Import routers directly from their modules
from .routers.auth_router import router as auth_router
from .routers.user_router import router as user_router
from .routers.company_router import router as company_router
from .routers.subscription_router import router as subscription_router
from .routers.query_log_router import router as query_log_router
from .routers.document_router import router as document_router
from .core.logging.middleware import RequestLoggingMiddleware
from .routers.rag_query_router import router as rag_router
import time

app = FastAPI(
    title="🚀 Nyro Backend API",
    description="""
    # Sistema RAG Multi-tenant
    
    API RESTful para gestión documental inteligente con arquitectura RAG.
    
    ## Características Principales
    
    * 🏢 **Multi-tenant**: Aislamiento seguro de datos por empresa
    * 📄 **Gestión Documental**: Procesamiento automático de documentos
    * 🤖 **RAG**: Consultas inteligentes usando Google Gemini
    * 🔐 **Seguridad**: Autenticación JWT y control de acceso por roles
    
    ## Guía Rápida
    
    1. Registra tu empresa y usuario
    2. Sube documentos
    3. Procesa los documentos
    4. Realiza consultas RAG
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "🔐 Operaciones de autenticación y gestión de usuarios"
        },
        {
            "name": "Companies",
            "description": "🏢 Gestión de empresas y configuración multi-tenant"
        },
        {
            "name": "Documents",
            "description": "📄 Gestión y procesamiento de documentos"
        },
        {
            "name": "RAG Queries",
            "description": "🤖 Consultas RAG sobre documentos procesados"
        },
        {
            "name": "Query Logs",
            "description": "📊 Registro y seguimiento de consultas"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Debug print to verify routers
print("Registering routers...")

# Include routers - note that these already have their prefixes defined
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(company_router)
app.include_router(subscription_router)
app.include_router(query_log_router)
app.include_router(document_router)
app.include_router(rag_router)

print("Routers registered!")

@app.get("/")
async def root():
    return {"message": "Welcome to Nyro API! See /docs for API documentation"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}