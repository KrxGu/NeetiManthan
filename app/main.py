from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import re
import uuid
from datetime import datetime
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import sentiment analysis with better error handling
try:
    from transformers import pipeline
    SENTIMENT_AVAILABLE = True
    logger.info("✅ Transformers library available")
except ImportError:
    SENTIMENT_AVAILABLE = False
    logger.warning("⚠️ Transformers library not available")

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

# Global variables
sentiment_pipeline = None
processed_comments = []
current_draft = None

# Create FastAPI app
app = FastAPI(
    title="NeetiManthan API (Fixed)",
    description="AI-Powered Public Comment Analysis System - Fixed ML Version",
    version="1.0.0-fixed",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_sentiment_model():
    """Load sentiment analysis pipeline with better error handling"""
    global sentiment_pipeline
    
    if not SENTIMENT_AVAILABLE:
        logger.warning("⚠️ Transformers not available, using fallback")
        return False
        
    try:
        logger.info("🔄 Loading sentiment analysis pipeline...")
        
        # Use pipeline which handles tokenizer issues better
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
            return_all_scores=True,
            device=-1,  # Use CPU
            framework="pt"
        )
        
        # Test the pipeline with a simple example
        test_result = sentiment_pipeline("This is a test.")
        logger.info(f"✅ Sentiment model loaded successfully. Test result: {test_result[0][0]['label']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load sentiment model: {e}")
        sentiment_pipeline = None
        return False

def analyze_sentiment(text: str) -> tuple:
    """Analyze sentiment with improved error handling"""
    if not sentiment_pipeline:
        return analyze_sentiment_fallback(text)
    
    try:
        # Truncate text to avoid tokenizer issues
        text_truncated = text[:500]  # Shorter limit for safety
        
        # Get predictions
        results = sentiment_pipeline(text_truncated)
        
        # Extract best prediction
        best_prediction = max(results[0], key=lambda x: x['score'])
        
        # Map labels to our format
        label_map = {
            'LABEL_0': 'negative',
            'LABEL_1': 'neutral', 
            'LABEL_2': 'positive',
            'NEGATIVE': 'negative',
            'NEUTRAL': 'neutral',
            'POSITIVE': 'positive'
        }
        
        sentiment = label_map.get(best_prediction['label'], best_prediction['label'].lower())
        confidence = float(best_prediction['score'])
        
        logger.info(f"📊 Sentiment analysis: {sentiment} ({confidence:.3f})")
        return sentiment, confidence
        
    except Exception as e:
        logger.error(f"❌ Sentiment analysis failed: {e}")
        return analyze_sentiment_fallback(text)

def analyze_sentiment_fallback(text: str) -> tuple:
    """Enhanced fallback sentiment analysis"""
    text_lower = text.lower()
    
    # Enhanced keyword lists
    positive_words = [
        "support", "good", "excellent", "appreciate", "reasonable", "efficient", 
        "helpful", "commendable", "beneficial", "welcome", "agree", "favor",
        "approve", "endorse", "praise", "outstanding", "effective", "valuable"
    ]
    
    negative_words = [
        "problematic", "harsh", "insufficient", "oppose", "concerned", "barriers", 
        "costs", "ambitious", "prohibitive", "vague", "disagree", "reject",
        "inadequate", "flawed", "unrealistic", "burden", "difficult", "challenging"
    ]
    
    # Count matches with context weighting
    positive_score = 0
    negative_score = 0
    
    for word in positive_words:
        if word in text_lower:
            # Give more weight to words at sentence boundaries
            if f" {word} " in text_lower or text_lower.startswith(word) or text_lower.endswith(word):
                positive_score += 2
            else:
                positive_score += 1
    
    for word in negative_words:
        if word in text_lower:
            if f" {word} " in text_lower or text_lower.startswith(word) or text_lower.endswith(word):
                negative_score += 2
            else:
                negative_score += 1
    
    # Determine sentiment with confidence
    if positive_score > negative_score:
        confidence = min(0.95, 0.6 + (positive_score - negative_score) * 0.05)
        return "positive", confidence
    elif negative_score > positive_score:
        confidence = min(0.95, 0.6 + (negative_score - positive_score) * 0.05)
        return "negative", confidence
    else:
        return "neutral", 0.5

def extract_mentioned_clauses(text: str) -> Optional[str]:
    """Enhanced clause extraction"""
    patterns = [
        r"Rule\s+(\d+(?:\([^)]+\))*)",
        r"rule\s+(\d+(?:\([^)]+\))*)",
        r"Section\s+(\d+(?:\([^)]+\))*)",
        r"section\s+(\d+(?:\([^)]+\))*)",
        r"Article\s+(\d+(?:\([^)]+\))*)",
        r"article\s+(\d+(?:\([^)]+\))*)",
        r"Clause\s+(\d+(?:\([^)]+\))*)",
        r"clause\s+(\d+(?:\([^)]+\))*)"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return f"Rule {matches[0]}"
    
    return None

@app.on_event("startup")
async def startup_event():
    """Initialize application with better startup handling"""
    logger.info("🚀 Starting NeetiManthan API (Fixed Version)")
    
    # Load sentiment model in background to avoid blocking startup
    try:
        model_loaded = load_sentiment_model()
        if model_loaded:
            logger.info("✅ ML-powered sentiment analysis ready")
        else:
            logger.warning("⚠️ Using enhanced rule-based sentiment analysis")
    except Exception as e:
        logger.error(f"❌ Error during model loading: {e}")

@app.get("/")
async def root():
    """Root endpoint with model status"""
    return {
        "message": "NeetiManthan API (Fixed ML Version)",
        "version": "1.0.0-fixed",
        "docs": "/docs",
        "status": "ready",
        "sentiment_analysis": "ml-powered" if sentiment_pipeline else "rule-based",
        "model_status": "loaded" if sentiment_pipeline else "fallback",
        "features": [
            "Fixed ML sentiment analysis",
            "Enhanced clause extraction", 
            "CSV upload support",
            "Real-time analytics",
            "Sample data processing",
            "Robust error handling"
        ]
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "sentiment_model": "ml-loaded" if sentiment_pipeline else "rule-based",
        "version": "1.0.0-fixed",
        "processed_comments": len(processed_comments),
        "model_type": "transformer" if sentiment_pipeline else "enhanced-rules"
    }

@app.post("/draft/upload")
async def upload_draft(draft: DraftInput):
    """Upload and process draft document"""
    global current_draft
    
    draft_id = str(uuid.uuid4())
    
    # Extract clauses with improved parsing
    lines = draft.content.split('\n')
    clauses = []
    
    for line in lines:
        line = line.strip()
        # Match various numbering patterns
        if re.match(r'^\d+\.', line) or re.match(r'^\(\d+\)', line) or re.match(r'^[A-Z]\)', line):
            clauses.append(line)
    
    current_draft = {
        "id": draft_id,
        "title": draft.title,
        "content": draft.content,
        "clauses": clauses,
        "created_at": datetime.now().isoformat()
    }
    
    logger.info(f"📄 Draft uploaded: {draft.title}, {len(clauses)} clauses extracted")
    
    return {
        "id": draft_id,
        "title": draft.title,
        "clauses_extracted": len(clauses),
        "clauses": clauses[:5],
        "status": "processed"
    }

@app.post("/comments/single", response_model=CommentResponse)
async def process_single_comment(comment: CommentInput):
    """Process single comment with improved error handling"""
    global processed_comments
    
    comment_id = str(uuid.uuid4())
    
    try:
        # Analyze sentiment
        sentiment, confidence = analyze_sentiment(comment.text)
        
        # Extract mentioned clauses
        mentioned_clause = extract_mentioned_clauses(comment.text)
        
        comment_data = {
            "id": comment_id,
            "text": comment.text,
            "sentiment": sentiment,
            "confidence": round(confidence, 3),
            "clause_mentioned": mentioned_clause,
            "user_type": comment.user_type,
            "organization": comment.organization,
            "state": comment.state,
            "processed_at": datetime.now().isoformat()
        }
        
        processed_comments.append(comment_data)
        
        logger.info(f"💬 Processed comment: {sentiment} ({confidence:.3f}) - {comment.text[:50]}...")
        
        return CommentResponse(**comment_data)
        
    except Exception as e:
        logger.error(f"❌ Error processing comment: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing comment: {str(e)}")

@app.post("/comments/upload-csv")
async def upload_comments_csv(file: UploadFile = File(...)):
    """Upload and process CSV file"""
    global processed_comments
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        new_comments = []
        for idx, row in df.iterrows():
            comment_id = str(uuid.uuid4())
            text = str(row['text'])
            
            # Process with error handling
            try:
                sentiment, confidence = analyze_sentiment(text)
                mentioned_clause = extract_mentioned_clauses(text)
                
                comment_data = {
                    "id": comment_id,
                    "text": text,
                    "sentiment": sentiment,
                    "confidence": round(confidence, 3),
                    "clause_mentioned": mentioned_clause,
                    "user_type": row.get('user_type'),
                    "organization": row.get('organization'),
                    "state": row.get('state'),
                    "processed_at": datetime.now().isoformat()
                }
                
                new_comments.append(comment_data)
                
            except Exception as e:
                logger.error(f"❌ Error processing row {idx}: {e}")
                continue
        
        processed_comments.extend(new_comments)
        
        logger.info(f"📊 Processed {len(new_comments)} comments from CSV")
        
        return {
            "message": f"Successfully processed {len(new_comments)} comments",
            "total_comments": len(processed_comments),
            "sample_results": new_comments[:3]
        }
        
    except Exception as e:
        logger.error(f"❌ CSV processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """Get comprehensive analytics"""
    if not processed_comments:
        raise HTTPException(status_code=404, detail="No comments processed yet")
    
    # Calculate metrics
    sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0
    clause_mentions = {}
    
    for comment in processed_comments:
        sentiment_dist[comment["sentiment"]] += 1
        total_confidence += comment["confidence"]
        
        if comment["clause_mentioned"]:
            clause = comment["clause_mentioned"]
            clause_mentions[clause] = clause_mentions.get(clause, 0) + 1
    
    top_clauses = [
        {"clause": clause, "mentions": count}
        for clause, count in sorted(clause_mentions.items(), key=lambda x: x[1], reverse=True)
    ]
    
    avg_confidence = total_confidence / len(processed_comments)
    
    return AnalyticsResponse(
        total_comments=len(processed_comments),
        processed_comments=len(processed_comments),
        sentiment_distribution=sentiment_dist,
        average_confidence=round(avg_confidence, 3),
        top_clauses=top_clauses[:10],
        processing_summary={
            "sentiment_model": "ml-transformer" if sentiment_pipeline else "enhanced-rules",
            "clauses_extracted": len(clause_mentions),
            "current_draft": current_draft["title"] if current_draft else None,
            "model_version": "cardiffnlp/twitter-roberta-base-sentiment-latest" if sentiment_pipeline else "rule-based-v2"
        }
    )

@app.get("/comments")
async def get_all_comments():
    """Get all processed comments"""
    return {
        "total_comments": len(processed_comments),
        "comments": processed_comments
    }

@app.get("/draft")
async def get_current_draft():
    """Get current draft"""
    if not current_draft:
        raise HTTPException(status_code=404, detail="No draft uploaded yet")
    return current_draft

@app.delete("/reset")
async def reset_data():
    """Reset all data"""
    global processed_comments, current_draft
    processed_comments = []
    current_draft = None
    logger.info("🔄 All data reset")
    return {"message": "All data reset successfully"}

@app.post("/test-sentiment")
async def test_sentiment_endpoint():
    """Test sentiment analysis with sample texts"""
    test_texts = [
        "I strongly support this excellent initiative",
        "This is problematic and creates unnecessary barriers", 
        "The timeline should be reviewed for clarity"
    ]
    
    results = []
    for text in test_texts:
        sentiment, confidence = analyze_sentiment(text)
        results.append({
            "text": text,
            "sentiment": sentiment,
            "confidence": round(confidence, 3)
        })
    
    return {
        "test_results": results,
        "model_type": "ml-transformer" if sentiment_pipeline else "enhanced-rules",
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
