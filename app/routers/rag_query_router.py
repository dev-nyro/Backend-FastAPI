from fastapi import APIRouter, Request, HTTPException, Depends
from ..models.rag_query_model import RAGQueryRequest, RAGQueryResponse
from ..auth.auth_middleware import auth_middleware
from ..config.database import get_supabase_client
from ..utils.document_processor import document_processor
from ..llm.gemini_client import gemini_client  # Add this import
from typing import Dict, Any
import time

router = APIRouter(
    prefix="/rag",
    tags=["RAG Queries"],
    dependencies=[Depends(auth_middleware)]
)

@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(query: RAGQueryRequest, request: Request):
    """
    Consulta RAG
    
    ### Descripción
    Realiza una consulta sobre los documentos procesados usando RAG.
    
    ### Proceso
    1. Búsqueda de chunks relevantes
    2. Generación de respuesta con Gemini
    3. Registro de la consulta
    
    ### Parámetros
    - **query**: Texto de la consulta
    - **max_results**: Número máximo de chunks a considerar
    
    ### Retorna
    - **query**: Consulta original
    - **relevant_chunks**: Fragmentos relevantes encontrados
    - **answer**: Respuesta generada por Gemini
    - **metadata**: Información adicional del proceso
    """
    start_time = time.time()
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # First get all document IDs belonging to the company
        docs_response = supabase.table('documents')\
            .select("id")\
            .eq('company_id', company_id)\
            .execute()
            
        if not docs_response.data:
            return {
                "query": query.query,
                "relevant_chunks": [],
                "answer": "No documents found",
                "metadata": {
                    "processing_time": f"{time.time() - start_time:.2f}s",
                    "total_chunks": 0,
                    "returned_chunks": 0
                }
            }
        
        # Get document IDs
        doc_ids = [doc['id'] for doc in docs_response.data]
        
        # Get chunks for these documents
        chunks_response = supabase.table('document_chunks')\
            .select("*")\
            .in_('document_id', doc_ids)\
            .execute()
            
        # For MVP, simple text matching
        relevant_chunks = [
            chunk for chunk in chunks_response.data
            if query.query.lower() in chunk['content'].lower()
        ][:query.max_results]
        
        # Generate LLM response using Gemini
        llm_response = await gemini_client.generate_response(
            query.query,
            relevant_chunks
        )
        
        response = {
            "query": query.query,
            "relevant_chunks": relevant_chunks,
            "answer": llm_response,  # Now using the LLM response
            "metadata": {
                "processing_time": f"{time.time() - start_time:.2f}s",
                "total_chunks": len(chunks_response.data),
                "returned_chunks": len(relevant_chunks)
            }
        }
        
        # Log the query
        await log_query(query.query, response, request)
        
        return response
        
    except Exception as e:
        print(f"Error in query_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def log_query(query: str, response: Dict[str, Any], request: Request):
    """Log the RAG query using existing query log system"""
    try:
        supabase = get_supabase_client(use_service_role=True)
        user = request.state.user
        
        log_data = {
            "user_id": user.get('user_id'),
            "company_id": user.get('company_id'),
            "query": query,
            "response": str(response["answer"]),
            "metadata": {
                "chunks_returned": len(response["relevant_chunks"]),
                "processing_time": response["metadata"]["processing_time"]
            }
        }
        
        supabase.table('query_logs').insert(log_data).execute()
        
    except Exception as e:
        print(f"Error logging query: {str(e)}")
        # Don't raise exception - logging failure shouldn't affect the query response