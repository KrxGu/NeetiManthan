"""
Text processing utilities
"""
import re
import unicodedata
from typing import List, Dict, Any

def normalize_text(text: str) -> str:
    """Normalize text for consistent processing"""
    if not text:
        return ""
    
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

def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """Extract keywords from text using simple heuristics"""
    if not text:
        return []
    
    # Convert to lowercase and extract words
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
    
    # Common stopwords
    stopwords = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
        'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
        'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
        'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
        'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
        'who', 'whom', 'whose', 'this', 'that', 'these', 'those', 'am', 'is',
        'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'should',
        'could', 'can', 'may', 'might', 'must', 'shall', 'should', 'ought'
    }
    
    # Filter out stopwords and count frequency
    word_freq = {}
    for word in words:
        if word not in stopwords:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in keywords[:max_keywords]]

def detect_language_simple(text: str) -> str:
    """Simple language detection based on character patterns"""
    if not text:
        return 'unknown'
    
    # Count different script characters
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    
    total_chars = len(re.sub(r'\s', '', text))
    
    if total_chars == 0:
        return 'unknown'
    
    # Simple heuristics
    if devanagari_chars / total_chars > 0.3:
        return 'hi'  # Hindi
    elif arabic_chars / total_chars > 0.3:
        return 'ur'  # Urdu
    elif latin_chars / total_chars > 0.7:
        return 'en'  # English
    else:
        return 'unknown'

def clean_text_for_display(text: str, max_length: int = 200) -> str:
    """Clean text for display in UI"""
    if not text:
        return ""
    
    # Normalize
    text = normalize_text(text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text

def extract_clause_references(text: str) -> List[str]:
    """Extract clause references from text"""
    references = []
    
    # Patterns to find clause references
    patterns = [
        r'(?i)(?:section|rule|chapter|part)\s+(\d+(?:\(\d+\))*(?:\([a-z]+\))*)',
        r'(?i)(?:clause|para|paragraph)\s+(\d+(?:\.\d+)*)',
        r'\b(\d+\.\d+(?:\.\d+)*)\b',  # Numbered references like 8.2.1
        r'\((\d+)\)\(([a-z]+)\)',     # References like (2)(b)
        r'\b(\d+)\([a-z]+\)',         # References like 8(b)
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            if len(match.groups()) == 1:
                ref = match.group(1)
            elif len(match.groups()) == 2:
                ref = f"{match.group(1)}({match.group(2)})"
            else:
                ref = match.group(0)
            
            if ref not in references:
                references.append(ref)
    
    return references
