from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, BackgroundTasks
from ..models.document_model import Document, DocumentCreate, DocumentUpdate, DocumentResponse, DocumentChunk
from ..config.database import get_supabase_client
from ..auth.auth_middleware import auth_middleware
from ..utils import storage
from ..utils.document_processor import document_processor
from ..utils.subscription_validator import check_document_limits
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import pytz

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],  # Capitalize to be consistent with other routers
    dependencies=[Depends(auth_middleware)]
)

@router.post("/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate, request: Request):
    """Create a new document"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        # Check subscription limits first
        await check_document_limits(company_id)
        
        supabase = get_supabase_client(use_service_role=True)
        
        # Prepare document data with correct fields based on schema
        now = datetime.now(pytz.UTC)
        document_data = {
            "company_id": company_id,
            "file_name": document.file_name,
            "file_type": document.file_type,
            "file_path": document.file_path,
            "metadata": document.metadata or {},
            "status": "uploaded",
            "chunk_count": 0,
            "uploaded_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        response = supabase.table('documents').insert(document_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create document")
        
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in create_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/", response_model=Document)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Subida de documento
    
    ### Descripción
    Sube un nuevo documento y lo almacena en Supabase Storage.
    
    ### Parámetros
    - **file**: Archivo a subir (PDF)
    - **metadata**: Metadatos adicionales del documento (opcional)
    
    ### Proceso
    1. Valida el archivo
    2. Sube a Supabase Storage
    3. Crea registro en base de datos
    4. Inicia procesamiento en segundo plano
    
    ### Retorna
    - Objeto Document con los detalles del documento creado
    """
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        # Check subscription limits before uploading
        await check_document_limits(company_id)
        
        # Upload to storage using the storage utility
        storage_path = await storage.upload_file(file, company_id)
        
        # Create document record
        document_data = {
            "company_id": company_id,
            "file_name": file.filename,
            "file_type": file.filename.split('.')[-1].lower(),
            "content_type": file.content_type,
            "file_size": file.size,
            "storage_path": storage_path,
            "metadata": metadata or {},
            "processing_status": "uploaded",
            "uploaded_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase = get_supabase_client(use_service_role=True)
        response = supabase.table('documents').insert(document_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create document")
            
        # Start async processing
        background_tasks.add_task(process_document, response.data[0]['id'])
        
        return response.data[0]
        
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(request: Request):
    """Get all documents for the company"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Get documents for company
        response = supabase.table('documents')\
            .select("*")\
            .eq('company_id', company_id)\
            .execute()
            
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID, request: Request):
    """Get a specific document"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        response = supabase.table('documents')\
            .select("*")\
            .eq('id', str(document_id))\
            .eq('company_id', company_id)\
            .execute()
            
        if not response.data:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: UUID, document: DocumentUpdate, request: Request):
    """Update a document's metadata or status"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Verify document exists and belongs to company
        existing = supabase.table('documents')\
            .select("*")\
            .eq('id', str(document_id))\
            .eq('company_id', company_id)\
            .execute()
            
        if not existing.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Prepare update data
        update_data = {}
        if document.file_name is not None:
            update_data["file_name"] = document.file_name
        if document.metadata is not None:
            update_data["metadata"] = document.metadata
        if document.status is not None:
            update_data["status"] = document.status
            
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table('documents')\
            .update(update_data)\
            .eq('id', str(document_id))\
            .eq('company_id', company_id)\
            .execute()
            
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: UUID, request: Request):
    """Delete a document"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Get document first to verify it exists and belongs to company
        document = supabase.table('documents')\
            .select("*")\
            .eq('id', str(document_id))\
            .eq('company_id', company_id)\
            .single()\
            .execute()
            
        if not document.data:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Delete document chunks first
        supabase.table('document_chunks')\
            .delete()\
            .eq('document_id', str(document_id))\
            .execute()
        
        # Then delete the document
        response = supabase.table('documents')\
            .delete()\
            .eq('id', str(document_id))\
            .execute()
            
        return {"message": "Document deleted successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/process")
async def process_document(
    document_id: UUID, 
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Procesar documento
    
    ### Descripción
    Inicia el pipeline de procesamiento de un documento.
    
    ### Etapas
    1. Extracción de texto
    2. Segmentación en chunks
    3. Generación de embeddings
    
    ### Parámetros
    - **document_id**: ID del documento a procesar
    
    ### Retorna
    - Estado del procesamiento iniciado
    """
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Get document first to verify it exists and belongs to company
        document = supabase.table('documents')\
            .select("*")\
            .eq('id', str(document_id))\
            .eq('company_id', company_id)\
            .single()\
            .execute()
            
        if not document.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # First check file type before doing anything else
        file_type = document.data.get('file_type', '').lower()
        if file_type == 'xyz':
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Update status to processing
        update_data = {
            "status": "processing",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table('documents')\
            .update(update_data)\
            .eq('id', str(document_id))\
            .execute()

        # Add background task with string ID
        background_tasks.add_task(
            document_processor.process_document,
            str(document_id)  # Convert UUID to string
        )
        
        return {"message": "Document processing started"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/chunks", response_model=List[DocumentChunk])
async def get_document_chunks(document_id: UUID, request: Request):
    """Get all chunks for a specific document"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Verify document exists and belongs to company
        document = supabase.table('documents')\
            .select("*")\
            .eq('id', str(document_id))\
            .eq('company_id', company_id)\
            .single()\
            .execute()
            
        if not document.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        response = supabase.table('document_chunks')\
            .select("*")\
            .eq('document_id', str(document_id))\
            .order('chunk_index')\
            .execute()
            
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Error fetching chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))