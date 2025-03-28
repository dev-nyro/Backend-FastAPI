from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class QueryLogBase(BaseModel):
    query: str
    response: Optional[str] = None
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = {}

class QueryLogCreate(QueryLogBase):
    pass

class QueryLogUpdate(BaseModel):
    response: Optional[str] = None
    relevance_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class QueryLog(QueryLogBase):
    id: UUID
    user_id: UUID
    company_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)