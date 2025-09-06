"""
Classify Tool - Sentiment, stance, and aspect classification
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import structlog
import os

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(title="Classify Tool", version="1.0.0")

# Model configuration
MODEL_ID = os.getenv("MODEL_ID", "cardiffnlp/twitter-xlm-roberta-base-sentiment")
MODEL_VERSION = "1.0.0"

# Load model and tokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()
    logger.info("Model loaded successfully", model_id=MODEL_ID)
except Exception as e:
    tokenizer = None
    model = None
    logger.error("Failed to load model", model_id=MODEL_ID, error=str(e))

# Label mappings
SENTIMENT_LABELS = {0: "negative", 1: "neutral", 2: "positive"}
STANCE_LABELS = {
    "positive": "supports",
    "negative": "opposes", 
    "neutral": "neutral"
}

# Aspect categories for policy comments
ASPECT_KEYWORDS = {
    "clarity": ["clear", "unclear", "confusing", "ambiguous", "vague", "specific"],
    "timelines": ["time", "deadline", "schedule", "delay", "urgent", "timeline"],
    "compliance_cost": ["cost", "expensive", "affordable", "budget", "financial", "burden"],
    "scope": ["scope", "coverage", "include", "exclude", "broad", "narrow"],
    "definitions": ["define", "definition", "meaning", "unclear", "specific", "terminology"],
    "enforcement": ["enforce", "penalty", "violation", "compliance", "monitoring"],
    "it_data": ["digital", "online", "data", "technology", "system", "portal"],
    "forms_process": ["form", "procedure", "process", "paperwork", "documentation"],
    "legal_consistency": ["law", "legal", "constitution", "conflict", "consistent"],
    "msme_impact": ["small", "medium", "startup", "msme", "business", "impact"]
}

class ClassifyRequest(BaseModel):
    text: str
    language: Optional[str] = None

class ClassifyResponse(BaseModel):
    sentiment_label: str
    sentiment_score: float
    sentiment_intensity: float
    stance: str
    aspects: List[str]
    confidence: float
    model_version: str
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None

class SentimentClassifier:
    """Sentiment classification with calibration"""
    
    def __init__(self):
        self.temperature = 1.0  # Will be calibrated later
    
    def predict(self, text: str) -> Dict[str, Any]:
        """Predict sentiment with confidence"""
        if not model or not tokenizer:
            raise ValueError("Model not loaded")
        
        # Tokenize and predict
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
            # Apply temperature scaling for calibration
            scaled_logits = logits / self.temperature
            probs = F.softmax(scaled_logits, dim=-1)[0].numpy()
        
        # Get prediction
        predicted_idx = int(np.argmax(probs))
        sentiment_label = SENTIMENT_LABELS[predicted_idx]
        sentiment_score = float(probs[predicted_idx])
        
        # Calculate intensity (distance from neutral)
        neutral_prob = probs[1]  # Neutral is index 1
        intensity = 1.0 - neutral_prob
        
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "sentiment_intensity": float(intensity),
            "probabilities": probs.tolist(),
            "confidence": sentiment_score
        }

class StanceClassifier:
    """Rule-based stance classification based on sentiment"""
    
    def predict(self, sentiment_label: str, text: str) -> str:
        """Predict stance based on sentiment and keywords"""
        # Basic mapping from sentiment to stance
        base_stance = STANCE_LABELS.get(sentiment_label, "neutral")
        
        # Look for explicit support/opposition keywords
        text_lower = text.lower()
        
        support_keywords = [
            "support", "agree", "good", "excellent", "approve", "endorse",
            "welcome", "appreciate", "favor", "positive", "beneficial"
        ]
        
        oppose_keywords = [
            "oppose", "disagree", "bad", "terrible", "reject", "against",
            "object", "protest", "negative", "harmful", "problematic"
        ]
        
        support_count = sum(1 for word in support_keywords if word in text_lower)
        oppose_count = sum(1 for word in oppose_keywords if word in text_lower)
        
        if support_count > oppose_count and support_count > 0:
            return "supports"
        elif oppose_count > support_count and oppose_count > 0:
            return "opposes"
        else:
            return base_stance

class AspectExtractor:
    """Extract policy aspects from text"""
    
    def extract(self, text: str) -> List[str]:
        """Extract relevant aspects from text"""
        text_lower = text.lower()
        detected_aspects = []
        
        for aspect, keywords in ASPECT_KEYWORDS.items():
            # Check if any keywords for this aspect are present
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                detected_aspects.append(aspect)
        
        return detected_aspects

# Initialize classifiers
sentiment_classifier = SentimentClassifier()
stance_classifier = StanceClassifier()
aspect_extractor = AspectExtractor()

def calculate_confidence_interval(confidence: float, n_samples: int = 100) -> tuple[float, float]:
    """Calculate confidence interval using bootstrap approximation"""
    # Simple approximation - in practice, you'd use bootstrap sampling
    margin = 1.96 * np.sqrt(confidence * (1 - confidence) / n_samples)
    ci_low = max(0.0, confidence - margin)
    ci_high = min(1.0, confidence + margin)
    return ci_low, ci_high

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION
    }

@app.post("/classify", response_model=ClassifyResponse)
async def classify_text(request: ClassifyRequest):
    """Classify text for sentiment, stance, and aspects"""
    try:
        text = request.text.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(text) > 5000:
            text = text[:5000]  # Truncate very long texts
        
        logger.info("Classifying text", text_length=len(text), language=request.language)
        
        # Step 1: Sentiment Classification
        sentiment_result = sentiment_classifier.predict(text)
        
        # Step 2: Stance Classification
        stance = stance_classifier.predict(sentiment_result["sentiment_label"], text)
        
        # Step 3: Aspect Extraction
        aspects = aspect_extractor.extract(text)
        
        # Step 4: Calculate confidence intervals
        confidence = sentiment_result["confidence"]
        ci_low, ci_high = calculate_confidence_interval(confidence)
        
        result = ClassifyResponse(
            sentiment_label=sentiment_result["sentiment_label"],
            sentiment_score=sentiment_result["sentiment_score"],
            sentiment_intensity=sentiment_result["sentiment_intensity"],
            stance=stance,
            aspects=aspects,
            confidence=confidence,
            model_version=MODEL_VERSION,
            ci_low=ci_low,
            ci_high=ci_high
        )
        
        logger.info(
            "Classification completed",
            sentiment=result.sentiment_label,
            stance=result.stance,
            aspects=result.aspects,
            confidence=result.confidence
        )
        
        return result
        
    except Exception as e:
        logger.error("Classification failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/calibrate")
async def calibrate_model(temperature: float = 1.0):
    """Update temperature for calibration"""
    global sentiment_classifier
    sentiment_classifier.temperature = temperature
    
    logger.info("Model calibrated", temperature=temperature)
    return {"message": f"Temperature updated to {temperature}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
