from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

class DocumentBase(BaseModel):
    file_name: str
    file_type: str
    file_path: str
    metadata: Optional[Dict[str, Any]] = Field(default={})

class DocumentCreate(DocumentBase):
    status: Optional[str] = "uploaded"
    chunk_count: Optional[int] = 0

class DocumentUpdate(BaseModel):
    file_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class Document(DocumentBase):
    id: UUID
    company_id: UUID
    status: str
    chunk_count: int = 0
    uploaded_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DocumentResponse(Document):
    pass

class DocumentChunk(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default={})
    embedding_id: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True