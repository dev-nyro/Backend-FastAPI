from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.user_model import User, UserResponse
from ..config.database import get_supabase_client
from ..auth.auth_middleware import auth_middleware
from typing import List
from uuid import UUID

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(auth_middleware)]
)

@router.get("/", response_model=List[UserResponse])
async def get_users(request: Request):
    """Get all users (admin only) or company users (normal user)"""
    user = request.state.user
    company_id = user.get('company_id')
    is_admin = user.get('role') == 'admin'
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Build query based on role
        query = supabase.table('users').select("*")
        
        # Regular users can only see users from their company
        if not is_admin:
            query = query.eq('company_id', company_id)
            
        response = query.execute()
        
        # Remove hashed_password from responses
        users = []
        for user_data in response.data:
            if 'hashed_password' in user_data:
                user_data.pop('hashed_password')
            users.append(user_data)
            
        return users
    except Exception as e:
        print(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: UUID, request: Request):
    """Get a specific user"""
    user = request.state.user
    company_id = user.get('company_id')
    is_admin = user.get('role') == 'admin'
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Build query based on role
        query = supabase.table('users').select("*").eq('id', str(user_id))
        
        # Regular users can only see users from their company
        if not is_admin:
            query = query.eq('company_id', company_id)
            
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Remove hashed_password from response
        user_data = response.data[0]
        if 'hashed_password' in user_data:
            user_data.pop('hashed_password')
            
        return {"data": user_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ['router']
