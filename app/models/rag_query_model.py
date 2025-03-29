from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RAGQueryRequest(BaseModel):
    query: str
    max_results: int = 5
    company_id: Optional[str] = None  # Will be filled from JWT

class RAGQueryResponse(BaseModel):
    query: str
    relevant_chunks: List[Dict[str, Any]]
    answer: str
    metadata: Dict[str, Any] = {}