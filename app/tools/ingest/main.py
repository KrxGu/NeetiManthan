"""
Ingest Tool - PII masking, language detection, text normalization
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import re
import unicodedata
# import fasttext  # Commented out for ARM64 compatibility
from sentence_transformers import SentenceTransformer
import structlog

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

app = FastAPI(title="Ingest Tool", version="1.0.0")

# Load models
# FastText disabled for ARM64 compatibility
lang_model = None
logger.warning("FastText language detection disabled for ARM64 compatibility")

try:
    # Load embedding model for comment embeddings
    embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
except Exception as e:
    embedding_model = None
    logger.warning("Embedding model not available", error=str(e))

class ProcessRequest(BaseModel):
    text: str

class ProcessResponse(BaseModel):
    pii_masked: str
    language: Optional[str]
    normalized_text: str
    embedding: Optional[list] = None
    confidence: float

class PIIMasker:
    """Mask PII in Indian context"""
    
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:\+91|91)?[-.\s]?[6-9]\d{9}',
            'aadhaar': r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',
            'pan': r'\b[A-Z]{5}\d{4}[A-Z]\b',
            'gst': r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z]\d\b',
            'pincode': r'\b\d{6}\b',
            'name_patterns': [
                r'\bMr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
                r'\bMs\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
                r'\bDr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            ]
        }
    
    def mask_text(self, text: str) -> str:
        """Apply PII masking to text"""
        masked = text
        
        # Email
        masked = re.sub(self.patterns['email'], '[EMAIL]', masked, flags=re.IGNORECASE)
        
        # Phone numbers
        masked = re.sub(self.patterns['phone'], '[PHONE]', masked)
        
        # Aadhaar numbers
        masked = re.sub(self.patterns['aadhaar'], '[AADHAAR]', masked)
        
        # PAN numbers
        masked = re.sub(self.patterns['pan'], '[PAN]', masked)
        
        # GST numbers
        masked = re.sub(self.patterns['gst'], '[GST]', masked)
        
        # PIN codes (be careful not to mask legitimate numbers)
        masked = re.sub(r'\bPIN[-.\s]*' + self.patterns['pincode'], 'PIN [PINCODE]', masked, flags=re.IGNORECASE)
        
        # Names with titles
        for pattern in self.patterns['name_patterns']:
            masked = re.sub(pattern, '[NAME]', masked)
        
        return masked

class TextNormalizer:
    """Normalize text for processing"""
    
    def normalize(self, text: str) -> str:
        """Normalize text"""
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Fix common spacing issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
        
        # Fix punctuation spacing
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        text = re.sub(r'([,;:])\s*', r'\1 ', text)
        
        # Remove extra whitespace
        text = text.strip()
        
        return text

# Initialize processors
pii_masker = PIIMasker()
text_normalizer = TextNormalizer()

def detect_language(text: str) -> tuple[Optional[str], float]:
    """Detect language of text"""
    if not lang_model:
        return None, 0.0
    
    try:
        # Clean text for language detection
        clean_text = re.sub(r'[^\w\s]', ' ', text[:1000])  # Use first 1000 chars
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if len(clean_text) < 10:
            return None, 0.0
        
        predictions = lang_model.predict(clean_text, k=1)
        lang_code = predictions[0][0].replace('__label__', '')
        confidence = float(predictions[1][0])
        
        return lang_code, confidence
    except Exception as e:
        logger.error("Language detection failed", error=str(e))
        return None, 0.0

def create_embedding(text: str) -> Optional[list]:
    """Create embedding for text"""
    if not embedding_model:
        return None
    
    try:
        embedding = embedding_model.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error("Embedding creation failed", error=str(e))
        return None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models": {
            "language_detection": lang_model is not None,
            "embeddings": embedding_model is not None
        }
    }

@app.post("/process", response_model=ProcessResponse)
async def process_text(request: ProcessRequest):
    """Process text through ingest pipeline"""
    try:
        text = request.text
        
        if not text or len(text.strip()) < 1:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        logger.info("Processing text", text_length=len(text))
        
        # Step 1: PII Masking
        pii_masked = pii_masker.mask_text(text)
        
        # Step 2: Language Detection
        language, lang_confidence = detect_language(pii_masked)
        
        # Step 3: Text Normalization
        normalized = text_normalizer.normalize(pii_masked)
        
        # Step 4: Create Embedding
        embedding = create_embedding(normalized)
        
        # Calculate overall confidence
        confidence = lang_confidence if language else 0.5
        
        result = ProcessResponse(
            pii_masked=pii_masked,
            language=language,
            normalized_text=normalized,
            embedding=embedding,
            confidence=confidence
        )
        
        logger.info(
            "Text processing completed",
            language=language,
            lang_confidence=lang_confidence,
            has_embedding=embedding is not None
        )
        
        return result
        
    except Exception as e:
        logger.error("Text processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
