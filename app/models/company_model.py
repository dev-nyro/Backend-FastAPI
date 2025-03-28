from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class Company(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class CompanyCreate(BaseModel):
    name: str
    email: EmailStr

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class CompanyList(BaseModel):
    """Response model for list of companies"""
    companies: List[Company]
    total: int
    
    model_config = ConfigDict(from_attributes=True)