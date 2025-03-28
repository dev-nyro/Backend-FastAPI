from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.query_log_model import QueryLog, QueryLogCreate, QueryLogUpdate
from ..config.database import get_supabase_client
from ..auth.auth_middleware import auth_middleware
from datetime import datetime
from typing import List
from uuid import UUID

router = APIRouter(
    prefix="/query-logs",
    tags=["Query Logs"],
    dependencies=[Depends(auth_middleware)]
)

@router.post("/", response_model=QueryLog)
async def create_query_log(log: QueryLogCreate, request: Request):
    """Create a new query log"""
    user = request.state.user
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        log_data = {
            "user_id": user.get('user_id'),
            "company_id": user.get('company_id'),
            "query": log.query,
            "response": log.response,
            "relevance_score": log.relevance_score,
            "metadata": log.metadata,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table('query_logs').insert(log_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create query log")
            
        return response.data[0]
        
    except Exception as e:
        print(f"Error creating query log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[QueryLog])
async def get_query_logs(
    request: Request,
    limit: int = 50,
    offset: int = 0
):
    """Get query logs for the company"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        response = supabase.table('query_logs')\
            .select("*")\
            .eq('company_id', company_id)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit)\
            .execute()
            
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Error fetching query logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{log_id}", response_model=QueryLog)
async def get_query_log(log_id: UUID, request: Request):
    """Get a specific query log"""
    user = request.state.user
    company_id = user.get('company_id')
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # First check if log exists
        response = supabase.table('query_logs')\
            .select("*")\
            .eq('id', str(log_id))\
            .eq('company_id', company_id)\
            .execute()
            
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Query log not found")
            
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching query log: {e}")
        # Only raise 404 if it's a "no rows" error
        if isinstance(e, dict) and e.get('code') == 'PGRST116':
            raise HTTPException(status_code=404, detail="Query log not found")
        raise HTTPException(status_code=500, detail=str(e))