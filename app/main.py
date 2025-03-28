from fastapi import FastAPI, HTTPException, Depends
from app.config.database import get_supabase_client
from pydantic import BaseModel, EmailStr, ConfigDict  # Add ConfigDict import
from typing import Optional, Dict, Any
from datetime import datetime
from app.routers.auth_router import router as auth_router
from app.routers.company_router import router as company_router
from app.auth.auth_middleware import auth_middleware
from uuid import UUID
from app.routers.document_router import router as document_router
from app.routers.subscription_router import router as subscription_router  # Nueva línea
from app.routers.query_log_router import router as query_log_router

app = FastAPI(title="Users API")

# Updated router mounting with correct prefixes and separate document router
app.include_router(auth_router)
app.include_router(company_router)
# Mount document router with explicit prefix
app.include_router(document_router, prefix="/documents")
app.include_router(subscription_router)
app.include_router(query_log_router)

# Initialize Supabase client with better error handling
try:
    supabase = get_supabase_client()
except Exception as e:
    print(f"Error initializing Supabase client: {str(e)}")
    raise

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: str
    role: str = "user"
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "test@example.com",
                "name": "John Doe",
                "role": "user"
            }
        }
    )

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str

class SuccessResponse(BaseModel):
    status: str = "success"
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

@app.get("/", response_model=SuccessResponse)
def read_root():
    return SuccessResponse(message="API is running")

@app.get("/test-supabase", response_model=SuccessResponse)
async def test_supabase():
    try:
        response = supabase.table('users').select("*").limit(1).execute()
        return SuccessResponse(message="Connected to Supabase")
    except Exception as e:
        print(f"Database error: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/users/", response_model=SuccessResponse, dependencies=[Depends(auth_middleware)])
async def create_user(user: User):
    try:
        existing = supabase.table('users').select("*").eq('email', user.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=400, 
                detail="User with this email already exists"
            )
        
        user_data = {
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        return SuccessResponse(
            data=response.data[0] if response.data else None,
            message="User created successfully"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error creating user: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=SuccessResponse, dependencies=[Depends(auth_middleware)])
async def get_user(user_id: str):
    try:
        # Convert string to UUID to validate format
        uuid_obj = UUID(user_id)
        
        # Debug logging
        print(f"Fetching user with ID: {user_id}")
        
        # Use service role for getting user data
        supabase = get_supabase_client(use_service_role=True)
        response = supabase.table('users').select("*").eq('id', str(uuid_obj)).execute()
        print(f"Database response: {response.data}")  # Debug info
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        return SuccessResponse(data=response.data[0])
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    except Exception as e:
        print(f"Error fetching user: {str(e)}")  # For debugging
        raise HTTPException(status_code=404, detail=f"User not found")