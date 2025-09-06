"""
Clause Linker Tool - Links comments to relevant clauses in drafts
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import re
import numpy as np
from sentence_transformers import SentenceTransformer
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

app = FastAPI(title="Clause Linker Tool", version="1.0.0")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/neetimanthan")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Load embedding model
try:
    embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    logger.info("Embedding model loaded successfully")
except Exception as e:
    embedding_model = None
    logger.error("Failed to load embedding model", error=str(e))

class LinkRequest(BaseModel):
    text: str
    draft_id: str

class ClauseCandidate(BaseModel):
    clause_ref: str
    clause_text: str
    similarity_score: float
    match_type: str  # 'exact', 'semantic', 'fuzzy'

class LinkResponse(BaseModel):
    clause_candidates: List[str]
    detailed_matches: List[ClauseCandidate]
    confidence: float

class ClauseLinker:
    """Links comments to relevant clauses using multiple strategies"""
    
    def __init__(self):
        self.similarity_threshold = 0.3
        self.max_candidates = 5
        
        # Regex patterns for direct clause mentions
        self.clause_patterns = [
            r'(?i)(?:section|rule|chapter|part)\s+(\d+(?:\(\d+\))*(?:\([a-z]+\))*)',
            r'(?i)(?:clause|para|paragraph)\s+(\d+(?:\.\d+)*)',
            r'\b(\d+\.\d+(?:\.\d+)*)\b',  # Numbered references like 8.2.1
            r'\((\d+)\)\(([a-z]+)\)',     # References like (2)(b)
            r'\b(\d+)\([a-z]+\)',         # References like 8(b)
        ]
    
    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def find_direct_mentions(self, text: str) -> List[str]:
        """Find direct clause references in text"""
        mentions = []
        text_lower = text.lower()
        
        for pattern in self.clause_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if len(match.groups()) == 1:
                    mention = match.group(1)
                elif len(match.groups()) == 2:
                    mention = f"{match.group(1)}({match.group(2)})"
                else:
                    mention = match.group(0)
                
                # Normalize the mention
                mention = self.normalize_reference(mention)
                if mention and mention not in mentions:
                    mentions.append(mention)
        
        return mentions
    
    def normalize_reference(self, ref: str) -> str:
        """Normalize clause reference"""
        if not ref:
            return ""
        
        # Remove extra whitespace and standardize format
        ref = re.sub(r'\s+', ' ', ref.strip())
        
        # Standardize common patterns
        ref = re.sub(r'(?i)section\s+', 'Section ', ref)
        ref = re.sub(r'(?i)rule\s+', 'Rule ', ref)
        ref = re.sub(r'(?i)chapter\s+', 'Chapter ', ref)
        ref = re.sub(r'(?i)part\s+', 'Part ', ref)
        
        return ref
    
    def get_draft_clauses(self, db: Session, draft_id: str) -> List[Dict[str, Any]]:
        """Get all clauses for a draft from database"""
        try:
            # Import here to avoid circular imports
            from app.models import Clause
            
            clauses = db.query(Clause).filter(Clause.draft_id == draft_id).all()
            
            clause_data = []
            for clause in clauses:
                clause_data.append({
                    'ref': clause.ref,
                    'text': clause.text,
                    'embedding': clause.embedding
                })
            
            return clause_data
            
        except Exception as e:
            logger.error("Failed to get draft clauses", draft_id=draft_id, error=str(e))
            return []
    
    def semantic_similarity_search(self, query_text: str, clauses: List[Dict[str, Any]]) -> List[ClauseCandidate]:
        """Find clauses using semantic similarity"""
        if not embedding_model or not clauses:
            return []
        
        try:
            # Create query embedding
            query_embedding = embedding_model.encode([query_text])[0]
            
            candidates = []
            for clause in clauses:
                if clause.get('embedding'):
                    # Convert embedding back to numpy array
                    clause_embedding = np.array(clause['embedding'])
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, clause_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(clause_embedding)
                    )
                    
                    if similarity > self.similarity_threshold:
                        candidates.append(ClauseCandidate(
                            clause_ref=clause['ref'],
                            clause_text=clause['text'][:200] + "..." if len(clause['text']) > 200 else clause['text'],
                            similarity_score=float(similarity),
                            match_type='semantic'
                        ))
            
            # Sort by similarity score
            candidates.sort(key=lambda x: x.similarity_score, reverse=True)
            return candidates[:self.max_candidates]
            
        except Exception as e:
            logger.error("Semantic similarity search failed", error=str(e))
            return []
    
    def fuzzy_text_matching(self, query_text: str, clauses: List[Dict[str, Any]]) -> List[ClauseCandidate]:
        """Find clauses using fuzzy text matching"""
        candidates = []
        query_words = set(query_text.lower().split())
        
        for clause in clauses:
            clause_words = set(clause['text'].lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(query_words.intersection(clause_words))
            union = len(query_words.union(clause_words))
            
            if union > 0:
                jaccard_sim = intersection / union
                
                if jaccard_sim > 0.1:  # Lower threshold for fuzzy matching
                    candidates.append(ClauseCandidate(
                        clause_ref=clause['ref'],
                        clause_text=clause['text'][:200] + "..." if len(clause['text']) > 200 else clause['text'],
                        similarity_score=jaccard_sim,
                        match_type='fuzzy'
                    ))
        
        # Sort by similarity score
        candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        return candidates[:self.max_candidates]
    
    def link_comment_to_clauses(self, text: str, draft_id: str) -> LinkResponse:
        """Main method to link comment to clauses"""
        db = self.get_db()
        try:
            # Step 1: Look for direct mentions
            direct_mentions = self.find_direct_mentions(text)
            
            # Step 2: Get all clauses for the draft
            clauses = self.get_draft_clauses(db, draft_id)
            
            if not clauses:
                logger.warning("No clauses found for draft", draft_id=draft_id)
                return LinkResponse(
                    clause_candidates=[],
                    detailed_matches=[],
                    confidence=0.0
                )
            
            all_candidates = []
            final_clause_refs = []
            
            # Step 3: If direct mentions found, try to match them to actual clauses
            if direct_mentions:
                for mention in direct_mentions:
                    # Look for exact matches
                    for clause in clauses:
                        if mention.lower() in clause['ref'].lower() or clause['ref'].lower() in mention.lower():
                            candidate = ClauseCandidate(
                                clause_ref=clause['ref'],
                                clause_text=clause['text'][:200] + "..." if len(clause['text']) > 200 else clause['text'],
                                similarity_score=1.0,
                                match_type='exact'
                            )
                            all_candidates.append(candidate)
                            if clause['ref'] not in final_clause_refs:
                                final_clause_refs.append(clause['ref'])
            
            # Step 4: If no direct matches, use semantic similarity
            if not all_candidates:
                semantic_candidates = self.semantic_similarity_search(text, clauses)
                all_candidates.extend(semantic_candidates)
                
                for candidate in semantic_candidates:
                    if candidate.clause_ref not in final_clause_refs:
                        final_clause_refs.append(candidate.clause_ref)
            
            # Step 5: If still no good matches, try fuzzy matching
            if not all_candidates or max(c.similarity_score for c in all_candidates) < 0.5:
                fuzzy_candidates = self.fuzzy_text_matching(text, clauses)
                all_candidates.extend(fuzzy_candidates)
                
                for candidate in fuzzy_candidates:
                    if candidate.clause_ref not in final_clause_refs:
                        final_clause_refs.append(candidate.clause_ref)
            
            # Calculate overall confidence
            if all_candidates:
                max_score = max(c.similarity_score for c in all_candidates)
                confidence = min(max_score, 1.0)
            else:
                confidence = 0.0
            
            # Limit to top candidates
            all_candidates = all_candidates[:self.max_candidates]
            final_clause_refs = final_clause_refs[:self.max_candidates]
            
            return LinkResponse(
                clause_candidates=final_clause_refs,
                detailed_matches=all_candidates,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error("Clause linking failed", error=str(e))
            return LinkResponse(
                clause_candidates=[],
                detailed_matches=[],
                confidence=0.0
            )
        finally:
            db.close()

# Initialize linker
clause_linker = ClauseLinker()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "embedding_model_loaded": embedding_model is not None,
        "database_connected": True  # TODO: Add actual DB health check
    }

@app.post("/link", response_model=LinkResponse)
async def link_comment(request: LinkRequest):
    """Link a comment to relevant clauses"""
    try:
        text = request.text.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if not request.draft_id:
            raise HTTPException(status_code=400, detail="Draft ID is required")
        
        logger.info("Linking comment to clauses", 
                   text_length=len(text), 
                   draft_id=request.draft_id)
        
        result = clause_linker.link_comment_to_clauses(text, request.draft_id)
        
        logger.info("Clause linking completed",
                   candidates_found=len(result.clause_candidates),
                   confidence=result.confidence)
        
        return result
        
    except Exception as e:
        logger.error("Clause linking failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Linking failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
