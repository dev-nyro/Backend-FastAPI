from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class DocumentBase(BaseModel):
    file_name: str
    file_type: str
    file_path: str
    metadata: Dict[str, Any] = {}

class Document(BaseModel):
    id: UUID
    company_id: UUID
    file_name: str
    file_type: str
    file_path: str
    metadata: Dict[str, Any] = {}
    chunk_count: int = 0
    uploaded_at: datetime
    updated_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)

class DocumentCreate(BaseModel):
    file_name: str
    file_type: str
    file_path: str
    metadata: Dict[str, Any] = {}

class DocumentUpdate(BaseModel):
    file_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class DocumentResponse(Document):
    pass

class DocumentChunk(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata: Dict[str, Any] = {}
    embedding_id: Optional[str] = None
    embedding_vector: Optional[List[float]] = None  # Changed to match schema
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)