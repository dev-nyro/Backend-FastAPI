from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    id: UUID
    company_id: UUID
    email: EmailStr
    full_name: str
    role: str  # Consider using Literal['admin', 'user', 'guest']
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Literal['admin', 'user', 'guest'] = 'user'
    company_id: UUID

class UserAuth(BaseModel):
    email: EmailStr
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict