from fastapi import FastAPI, HTTPException
from supabase import create_client
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from datetime import datetime

load_dotenv()

app = FastAPI(title="Users API")

# Inicializar cliente de Supabase con mejor manejo de errores
try:
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
except Exception as e:
    print(f"Error initializing Supabase client: {str(e)}")
    raise

# Actualizar el modelo User para reflejar la estructura real de la tabla
class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: str
    role: str = "user"
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "test@example.com",
                "name": "John Doe",
                "role": "user"
            }
        }

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
        response = supabase.table('Users').select("*").limit(1).execute()
        return SuccessResponse(message="Connected to Supabase")
    except Exception as e:
        print(f"Database error: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Modificar el endpoint de creación para manejar los campos automáticos
@app.post("/users/", response_model=SuccessResponse)
async def create_user(user: User):
    try:
        # Verificar si el usuario ya existe
        existing = supabase.table('Users').select("*").eq('email', user.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=400, 
                detail="User with this email already exists"
            )
        
        # Omitimos id y created_at ya que son manejados por Supabase
        user_data = {
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
        
        response = supabase.table('Users').insert(user_data).execute()
        
        return SuccessResponse(
            data=response.data[0] if response.data else None,
            message="User created successfully"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error creating user: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=SuccessResponse)
async def get_user(user_id: str):
    try:
        response = supabase.table('Users').select("*").eq('id', user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        return SuccessResponse(data=response.data[0])
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching user: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=str(e))