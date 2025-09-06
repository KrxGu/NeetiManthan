from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class CommentCreate(BaseModel):
    draft_id: UUID
    text_raw: str = Field(..., min_length=1)
    user_meta: Optional[Dict[str, Any]] = None

class CommentResponse(BaseModel):
    id: UUID
    draft_id: UUID
    text_raw: str
    lang: Optional[str]
    pii_masked: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    id: UUID
    comment_id: UUID
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    sentiment_intensity: Optional[float]
    stance: Optional[str]
    aspects: Optional[List[str]]
    confidence: float
    model_version: str
    ci_low: Optional[float]
    ci_high: Optional[float]
    
    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    id: UUID
    comment_id: UUID
    summary_text: str
    confidence: float
    model_version: str
    
    class Config:
        from_attributes = True

class CommentWithAnalysis(CommentResponse):
    predictions: Optional[PredictionResponse] = None
    summaries: Optional[List[SummaryResponse]] = []
    clause_guesses: Optional[List[str]] = []

class CommentBulkUpload(BaseModel):
    draft_id: UUID
    comments: List[Dict[str, Any]] = Field(..., min_items=1)
    
class CommentFilter(BaseModel):
    draft_id: Optional[UUID] = None
    sentiment: Optional[str] = None
    stance: Optional[str] = None
    clause_ref: Optional[str] = None
    min_confidence: Optional[float] = None
    lang: Optional[str] = None
