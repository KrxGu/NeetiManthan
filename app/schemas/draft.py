from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class DraftCreate(BaseModel):
    title: str = Field(..., max_length=500)
    content: str = Field(..., min_length=1)
    text_uri: Optional[str] = Field(None, max_length=1000)

class DraftResponse(BaseModel):
    id: UUID
    title: str
    text_uri: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ClauseResponse(BaseModel):
    id: UUID
    draft_id: UUID
    ref: str
    text: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DraftWithClauses(DraftResponse):
    clauses: List[ClauseResponse] = []
