"""
Draft Processor - Extracts clauses from draft documents and creates embeddings
"""
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import structlog
from uuid import UUID

logger = structlog.get_logger()

class DraftProcessor:
    """Process draft documents to extract clauses"""
    
    def __init__(self):
        # Load embedding model
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        )
        
        # Clause patterns for Indian legal documents
        self.clause_patterns = [
            # Standard numbered clauses: 1., 2., etc.
            r'^\s*(\d+)\.\s+(.+?)(?=^\s*\d+\.|$)',
            # Sub-clauses: (a), (b), (i), (ii), etc.
            r'^\s*\(([a-z]+|[ivx]+)\)\s+(.+?)(?=^\s*\([a-z]+|[ivx]+\)|^\s*\d+\.|$)',
            # Legal section references: Section 8(2)(b)
            r'(Section\s+\d+(?:\(\d+\))*(?:\([a-z]+\))*)\s*[:\-]?\s*(.+?)(?=Section\s+\d+|$)',
            # Rule references: Rule 8, Rule 8(2), etc.
            r'(Rule\s+\d+(?:\(\d+\))*(?:\([a-z]+\))*)\s*[:\-]?\s*(.+?)(?=Rule\s+\d+|$)',
            # Chapter/Part references
            r'(Chapter\s+[IVX]+|Part\s+[IVX]+)\s*[:\-]?\s*(.+?)(?=Chapter\s+|Part\s+|$)',
        ]
    
    async def extract_clauses(self, content: str, draft_id: UUID) -> List[Dict[str, Any]]:
        """
        Extract clauses from draft content and create embeddings
        """
        logger.info("Extracting clauses from draft", draft_id=str(draft_id))
        
        clauses = []
        content = content.strip()
        
        # Try different extraction strategies
        extracted_clauses = []
        
        # Strategy 1: Use regex patterns
        for pattern in self.clause_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            for match in matches:
                ref = match.group(1).strip()
                text = match.group(2).strip()
                
                if len(text) > 20:  # Filter out very short clauses
                    extracted_clauses.append({
                        "ref": ref,
                        "text": text[:2000],  # Limit text length
                        "extraction_method": "regex"
                    })
        
        # Strategy 2: If regex doesn't work well, fall back to paragraph splitting
        if len(extracted_clauses) < 3:
            paragraphs = content.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                if len(paragraph) > 50:  # Filter short paragraphs
                    # Try to extract a reference from the beginning
                    ref_match = re.match(r'^(\d+\.|\([a-z]+\)|Section\s+\d+|Rule\s+\d+)', paragraph)
                    ref = ref_match.group(1) if ref_match else f"Para-{i+1}"
                    
                    extracted_clauses.append({
                        "ref": ref,
                        "text": paragraph[:2000],
                        "extraction_method": "paragraph"
                    })
        
        # Strategy 3: If still no clauses, create one clause for the entire document
        if len(extracted_clauses) == 0:
            extracted_clauses.append({
                "ref": "Full-Document",
                "text": content[:2000],
                "extraction_method": "full_document"
            })
        
        # Create embeddings for all clauses
        texts = [clause["text"] for clause in extracted_clauses]
        embeddings = self.embedding_model.encode(texts)
        
        # Combine clause data with embeddings
        for i, clause in enumerate(extracted_clauses):
            clauses.append({
                "ref": clause["ref"],
                "text": clause["text"],
                "embedding": embeddings[i].tolist(),  # Convert numpy array to list
                "extraction_method": clause["extraction_method"]
            })
        
        logger.info(
            "Clause extraction completed",
            draft_id=str(draft_id),
            clauses_count=len(clauses),
            methods_used=list(set(c["extraction_method"] for c in clauses))
        )
        
        return clauses
    
    def normalize_clause_reference(self, ref: str) -> str:
        """Normalize clause references for consistent matching"""
        # Remove extra whitespace
        ref = re.sub(r'\s+', ' ', ref.strip())
        
        # Normalize common patterns
        ref = re.sub(r'Section\s+', 'Section ', ref, flags=re.IGNORECASE)
        ref = re.sub(r'Rule\s+', 'Rule ', ref, flags=re.IGNORECASE)
        ref = re.sub(r'Chapter\s+', 'Chapter ', ref, flags=re.IGNORECASE)
        ref = re.sub(r'Part\s+', 'Part ', ref, flags=re.IGNORECASE)
        
        return ref
    
    def find_clause_mentions(self, text: str) -> List[str]:
        """
        Find clause references mentioned in comment text
        """
        mentions = []
        
        # Patterns to find clause references in comments
        mention_patterns = [
            r'(?:Section|Rule|Chapter|Part)\s+\d+(?:\(\d+\))*(?:\([a-z]+\))*',
            r'(?:clause|para|paragraph)\s+\d+(?:\.\d+)*',
            r'\d+\.\d+(?:\.\d+)*',  # Numbered references like 8.2.1
            r'\(\d+\)\([a-z]+\)',    # References like (2)(b)
        ]
        
        for pattern in mention_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                mention = self.normalize_clause_reference(match.group(0))
                if mention not in mentions:
                    mentions.append(mention)
        
        return mentions
