from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "user"

class UserAuth(UserBase):
    password: str

class UserCreate(UserBase):
    password: str
    company_id: UUID

class User(UserBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict