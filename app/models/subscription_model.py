from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class SubscriptionBase(BaseModel):
    plan_type: Literal['free', 'pro', 'enterprise']
    max_documents: int = Field(gt=0)
    max_queries: int = Field(gt=0)

    model_config = ConfigDict(from_attributes=True)

class SubscriptionCreate(BaseModel):
    company_id: UUID
    plan_type: Literal['free', 'pro', 'enterprise']
    max_documents: int = Field(gt=0)
    max_queries: int = Field(gt=0)
    start_date: datetime
    end_date: datetime

class SubscriptionUpdate(BaseModel):
    plan_type: Optional[Literal['free', 'pro', 'enterprise']] = None
    max_documents: Optional[int] = Field(None, gt=0)
    max_queries: Optional[int] = Field(None, gt=0)
    end_date: Optional[datetime] = None

class Subscription(SubscriptionBase):
    id: UUID
    company_id: UUID
    start_date: datetime
    end_date: datetime
    max_documents: int
    max_queries: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)