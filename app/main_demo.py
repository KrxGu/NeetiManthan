"""
NeetiManthan Demo API - Fast startup with mock data for UI testing
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import re
import uuid
from datetime import datetime
import random
from sqlalchemy.orm import Session

# Database imports
from app.core.database import get_db, init_db
from app.models.draft import Draft
from app.models.comment import Comment

try:
    init_db()
except Exception as e:
    print(f"Error initializing DB: {e}")

app = FastAPI(
    title="NeetiManthan API",
    description="AI-powered public comment analysis for draft laws (Demo Mode)",
    version="1.0.0-demo"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CommentInput(BaseModel):
    text: str
    user_type: Optional[str] = None
    organization: Optional[str] = None
    state: Optional[str] = None

class DraftInput(BaseModel):
    title: str
    content: str

class CommentResponse(BaseModel):
    id: str
    text: str
    sentiment: str
    confidence: float
    clause_mentioned: Optional[str] = None
    user_type: Optional[str] = None
    organization: Optional[str] = None
    state: Optional[str] = None
    processed_at: str

class AnalyticsResponse(BaseModel):
    total_comments: int
    processed_comments: int
    sentiment_distribution: Dict[str, int]
    average_confidence: float
    top_clauses: List[Dict[str, Any]]
    processing_summary: Dict[str, Any]

# In-memory storage
comments_db: List[Dict] = []
current_draft: Optional[Dict] = None

def mock_sentiment_analysis(text: str) -> tuple[str, float]:
    """Mock sentiment analysis with random but realistic results"""
    sentiments = ['positive', 'negative', 'neutral']
    weights = [0.3, 0.2, 0.5]  # More neutral comments
    sentiment = random.choices(sentiments, weights=weights)[0]
    confidence = random.uniform(0.6, 0.95)
    return sentiment, confidence

def extract_clauses(content: str) -> List[str]:
    """Extract clauses from draft content"""
    # Simple regex to find numbered sections
    pattern = r'(\d+\..*?)(?=\n\d+\.|\n\([a-z]\)|\n\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        # Fallback: split by lines and take first few meaningful ones
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return lines[:5] if len(lines) > 5 else lines
    
    return [match.strip() for match in matches[:10]]  # Limit to 10 clauses

@app.get("/")
async def root():
    return {
        "message": "NeetiManthan API (Demo Mode)",
        "version": "1.0.0-demo",
        "docs": "/docs",
        "status": "ready",
        "sentiment_analysis": "mock",
        "features": [
            "Mock sentiment analysis",
            "Clause extraction", 
            "CSV upload",
            "Fast startup"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "sentiment_model": "mock-loaded",
        "version": "1.0.0-demo",
        "processed_comments": len(comments_db)
    }

@app.post("/draft/upload")
async def upload_draft(draft_input: DraftInput, db: Session = Depends(get_db)):
    # Delete old comments and drafts to keep only one active for demo purposes
    db.query(Comment).delete()
    db.query(Draft).delete()
    db.commit()

    clauses = extract_clauses(draft_input.content)
    
    new_draft = Draft(
        title=draft_input.title,
        content=draft_input.content,
        clauses_extracted=len(clauses),
        clauses=clauses,
    )
    db.add(new_draft)
    db.commit()
    db.refresh(new_draft)
    
    return {
        "id": str(new_draft.id),
        "title": new_draft.title,
        "clauses_extracted": new_draft.clauses_extracted,
        "clauses": new_draft.clauses
    }


@app.get("/draft")
async def get_current_draft(db: Session = Depends(get_db)):
    latest_draft = db.query(Draft).order_by(Draft.created_at.desc()).first()
    if not latest_draft:
        raise HTTPException(status_code=404, detail="No draft uploaded yet")
    return latest_draft

@app.post("/comments/single")
async def process_single_comment(comment: CommentInput, db: Session = Depends(get_db)):
    latest_draft = db.query(Draft).order_by(Draft.created_at.desc()).first()

    sentiment, confidence = mock_sentiment_analysis(comment.text)
    
    # Mock clause linking
    clause_mentioned = None
    if latest_draft and latest_draft.clauses:
        # Randomly assign a clause for demo
        if random.random() > 0.3:  # 70% chance of clause assignment
            clause_mentioned = random.choice(latest_draft.clauses)
    
    comment_record = Comment(
        text=comment.text,
        sentiment=sentiment,
        confidence=confidence,
        clause_mentioned=clause_mentioned,
        user_type=comment.user_type,
        organization=comment.organization,
        state=comment.state,
        draft_id=latest_draft.id if latest_draft else None
    )
    
    db.add(comment_record)
    db.commit()
    db.refresh(comment_record)

    return comment_record

@app.post("/comments/upload-csv")
async def upload_comments_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    latest_draft = db.query(Draft).order_by(Draft.created_at.desc()).first()
    
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    
    processed_comments = []
    
    for _, row in df.iterrows():
        text = str(row.get('text', ''))
        if not text or text == 'nan':
            continue
            
        sentiment, confidence = mock_sentiment_analysis(text)
        
        # Mock clause linking
        clause_mentioned = None
        if latest_draft and latest_draft.clauses:
            if random.random() > 0.3:  # 70% chance of clause assignment
                clause_mentioned = random.choice(latest_draft.clauses)
        
        comment_record = Comment(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            clause_mentioned=clause_mentioned,
            user_type=str(row.get('user_type', '')),
            organization=str(row.get('organization', '')),
            state=str(row.get('state', '')),
            draft_id=latest_draft.id if latest_draft else None
        )
        
        db.add(comment_record)
        processed_comments.append(comment_record)
    
    db.commit()

    return {
        "message": f"Successfully processed {len(processed_comments)} comments",
        "total_comments": len(processed_comments),
    }

@app.get("/comments")
async def get_all_comments(db: Session = Depends(get_db)):
    all_comments = db.query(Comment).order_by(Comment.created_at.desc()).all()
    return {
        "comments": all_comments,
        "total": len(all_comments)
    }

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    all_comments = db.query(Comment).all()
    latest_draft = db.query(Draft).order_by(Draft.created_at.desc()).first()

    if not all_comments:
        # Return a default empty response instead of 404
        return AnalyticsResponse(
            total_comments=0,
            processed_comments=0,
            sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
            average_confidence=0.0,
            top_clauses=[],
            processing_summary={
                "sentiment_model": "mock",
                "clauses_extracted": latest_draft.clauses_extracted if latest_draft else 0,
                "current_draft": latest_draft.title if latest_draft else None
            }
        )
    
    # Calculate sentiment distribution
    sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0
    clause_mentions = {}
    
    for comment in all_comments:
        sentiment = comment.sentiment
        sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1
        total_confidence += comment.confidence
        
        if comment.clause_mentioned:
            clause = comment.clause_mentioned
            clause_mentions[clause] = clause_mentions.get(clause, 0) + 1
    
    # Top clauses
    top_clauses = [
        {"clause": clause, "mentions": count}
        for clause, count in sorted(clause_mentions.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return AnalyticsResponse(
        total_comments=len(all_comments),
        processed_comments=len(all_comments),
        sentiment_distribution=sentiment_dist,
        average_confidence=total_confidence / len(all_comments),
        top_clauses=top_clauses,
        processing_summary={
            "sentiment_model": "mock",
            "clauses_extracted": latest_draft.clauses_extracted if latest_draft else 0,
            "current_draft": latest_draft.title if latest_draft else None
        }
    )

@app.get("/test-sentiment")
async def test_sentiment():
    """Test endpoint for sentiment analysis"""
    test_texts = [
        "I strongly support this rule as it will benefit small businesses.",
        "This regulation is too restrictive and will hurt innovation.",
        "The proposed changes seem reasonable and well-balanced."
    ]
    
    results = []
    for text in test_texts:
        sentiment, confidence = mock_sentiment_analysis(text)
        results.append({
            "text": text,
            "sentiment": sentiment,
            "confidence": confidence
        })
    
    return {"results": results}

@app.delete("/reset")
async def reset_data(db: Session = Depends(get_db)):
    """Reset all data for testing"""
    db.query(Comment).delete()
    db.query(Draft).delete()
    db.commit()
    return {"message": "All data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
