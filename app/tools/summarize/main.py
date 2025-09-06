"""
Summarize Tool - Generate neutral summaries of comments
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
import structlog
import os
import re

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

app = FastAPI(title="Summarize Tool", version="1.0.0")

# Model configuration
MODEL_ID = os.getenv("SUMMARIZE_MODEL", "google/mt5-small")
MODEL_VERSION = "1.0.0"

# Load model and tokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
    
    # Create summarization pipeline
    summarizer = pipeline(
        "summarization",
        model=model,
        tokenizer=tokenizer,
        device=0 if torch.cuda.is_available() else -1,
        framework="pt"
    )
    
    logger.info("Summarization model loaded successfully", model_id=MODEL_ID)
except Exception as e:
    summarizer = None
    logger.error("Failed to load summarization model", model_id=MODEL_ID, error=str(e))

class SummarizeRequest(BaseModel):
    text: str
    clause_ref: Optional[str] = None
    max_length: Optional[int] = 100
    min_length: Optional[int] = 20

class SummarizeResponse(BaseModel):
    summary: str
    confidence: float
    model_version: str
    word_count: int
    compression_ratio: float

class CommentSummarizer:
    """Generate neutral summaries of policy comments"""
    
    def __init__(self):
        self.max_input_length = 1024
        self.template_patterns = {
            "supports": "The commenter supports {clause} stating that {content}",
            "opposes": "The commenter opposes {clause} arguing that {content}",
            "neutral": "The commenter notes regarding {clause} that {content}",
            "general": "The comment states that {content}"
        }
    
    def detect_stance_keywords(self, text: str) -> str:
        """Detect stance from text to choose appropriate template"""
        text_lower = text.lower()
        
        support_keywords = [
            "support", "agree", "good", "excellent", "approve", "endorse",
            "welcome", "appreciate", "favor", "positive", "beneficial", "helpful"
        ]
        
        oppose_keywords = [
            "oppose", "disagree", "bad", "terrible", "reject", "against",
            "object", "protest", "negative", "harmful", "problematic", "wrong"
        ]
        
        support_count = sum(1 for word in support_keywords if word in text_lower)
        oppose_count = sum(1 for word in oppose_keywords if word in text_lower)
        
        if support_count > oppose_count and support_count > 0:
            return "supports"
        elif oppose_count > support_count and oppose_count > 0:
            return "opposes"
        else:
            return "neutral"
    
    def clean_text_for_summarization(self, text: str) -> str:
        """Clean and prepare text for summarization"""
        # Remove PII markers
        text = re.sub(r'\[EMAIL\]|\[PHONE\]|\[AADHAAR\]|\[PAN\]|\[GST\]|\[NAME\]|\[PINCODE\]', '[REDACTED]', text)
        
        # Fix common issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)  # Sentence spacing
        
        # Truncate if too long
        if len(text) > self.max_input_length:
            text = text[:self.max_input_length] + "..."
        
        return text.strip()
    
    def extract_key_points(self, text: str) -> str:
        """Extract key points from text using simple heuristics"""
        sentences = re.split(r'[.!?]+', text)
        
        # Score sentences based on importance indicators
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            score = 0
            sentence_lower = sentence.lower()
            
            # Boost sentences with policy-relevant keywords
            policy_keywords = [
                "should", "must", "recommend", "suggest", "propose", "important",
                "necessary", "required", "mandatory", "optional", "clarify",
                "modify", "change", "improve", "concern", "issue", "problem"
            ]
            
            for keyword in policy_keywords:
                if keyword in sentence_lower:
                    score += 1
            
            # Boost sentences with numbers (often contain specific points)
            if re.search(r'\d+', sentence):
                score += 0.5
            
            # Penalize very short or very long sentences
            if len(sentence) < 20:
                score -= 0.5
            elif len(sentence) > 200:
                score -= 0.3
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:3]]  # Top 3 sentences
        
        return " ".join(top_sentences)
    
    def generate_template_summary(self, text: str, clause_ref: Optional[str] = None) -> tuple[str, float]:
        """Generate summary using templates"""
        try:
            stance = self.detect_stance_keywords(text)
            key_content = self.extract_key_points(text)
            
            if not key_content:
                key_content = text[:200] + "..." if len(text) > 200 else text
            
            # Choose template
            if clause_ref and stance in self.template_patterns:
                template = self.template_patterns[stance]
                summary = template.format(
                    clause=clause_ref,
                    content=key_content.lower()
                )
            else:
                template = self.template_patterns["general"]
                summary = template.format(content=key_content.lower())
            
            # Ensure summary is not too long
            if len(summary) > 200:
                summary = summary[:197] + "..."
            
            # Calculate confidence based on content quality
            confidence = 0.7  # Base confidence for template-based summaries
            if len(key_content) > 50:
                confidence += 0.1
            if clause_ref:
                confidence += 0.1
            
            confidence = min(confidence, 0.95)
            
            return summary, confidence
            
        except Exception as e:
            logger.error("Template summary generation failed", error=str(e))
            return f"Comment discusses {clause_ref or 'the policy'}.", 0.3
    
    def generate_model_summary(self, text: str, max_length: int = 100, min_length: int = 20) -> tuple[str, float]:
        """Generate summary using the ML model"""
        if not summarizer:
            return self.generate_template_summary(text)[0], 0.5
        
        try:
            # Prepare text
            clean_text = self.clean_text_for_summarization(text)
            
            # Generate summary
            result = summarizer(
                clean_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                num_beams=4,
                early_stopping=True
            )
            
            summary = result[0]['summary_text']
            
            # Calculate confidence based on summary quality
            confidence = 0.8  # Base confidence for model summaries
            
            # Adjust based on summary characteristics
            if len(summary) < 10:
                confidence -= 0.3
            elif len(summary.split()) < 5:
                confidence -= 0.2
            
            # Check if summary makes sense (basic heuristics)
            if summary.count('.') == 0 and len(summary) > 50:
                confidence -= 0.1
            
            confidence = max(0.1, min(confidence, 0.95))
            
            return summary, confidence
            
        except Exception as e:
            logger.error("Model summary generation failed", error=str(e))
            # Fallback to template
            return self.generate_template_summary(text)
    
    def summarize(self, text: str, clause_ref: Optional[str] = None, 
                  max_length: int = 100, min_length: int = 20) -> Dict[str, Any]:
        """Main summarization method"""
        
        original_word_count = len(text.split())
        
        # Try model-based summarization first, fall back to template
        if summarizer and len(text) > 100:
            summary, confidence = self.generate_model_summary(text, max_length, min_length)
        else:
            summary, confidence = self.generate_template_summary(text, clause_ref)
        
        summary_word_count = len(summary.split())
        compression_ratio = summary_word_count / original_word_count if original_word_count > 0 else 1.0
        
        return {
            "summary": summary,
            "confidence": confidence,
            "word_count": summary_word_count,
            "compression_ratio": compression_ratio
        }

# Initialize summarizer
comment_summarizer = CommentSummarizer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": summarizer is not None,
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_comment(request: SummarizeRequest):
    """Generate a neutral summary of a comment"""
    try:
        text = request.text.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(text) < 10:
            raise HTTPException(status_code=400, detail="Text too short to summarize")
        
        logger.info("Summarizing comment", 
                   text_length=len(text), 
                   clause_ref=request.clause_ref)
        
        result = comment_summarizer.summarize(
            text=text,
            clause_ref=request.clause_ref,
            max_length=request.max_length or 100,
            min_length=request.min_length or 20
        )
        
        response = SummarizeResponse(
            summary=result["summary"],
            confidence=result["confidence"],
            model_version=MODEL_VERSION,
            word_count=result["word_count"],
            compression_ratio=result["compression_ratio"]
        )
        
        logger.info("Summarization completed",
                   summary_length=len(response.summary),
                   confidence=response.confidence,
                   compression_ratio=response.compression_ratio)
        
        return response
        
    except Exception as e:
        logger.error("Summarization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
