"""
Coordinator Agent - Orchestrates the processing pipeline for comments
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import httpx
import structlog
from uuid import UUID

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.celery import celery_app
from app.models import CommentRaw, CommentProcessed, Prediction, Summary, Audit

logger = structlog.get_logger()

class CoordinatorAgent:
    """
    Central coordinator that orchestrates comment processing through various tools
    """
    
    def __init__(self):
        self.confidence_threshold = settings.confidence_threshold
        self.tool_urls = {
            "ingest": settings.ingest_tool_url,
            "classify": settings.classify_tool_url,
            "clause_linker": settings.clause_linker_url,
            "summarize": settings.summarize_tool_url,
        }
    
    async def process_comment(self, comment_id: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Main processing pipeline for a comment
        
        Flow:
        1. Ingest (PII masking, language detection, normalization)
        2. Clause linking (if no clause mentioned)
        3. Classification (sentiment, stance, aspects)
        4. Quality check (confidence threshold)
        5. Summarization (if confidence OK)
        6. Deduplication
        7. Keyword extraction
        8. Aggregation
        """
        db = SessionLocal()
        try:
            comment = db.query(CommentRaw).filter(CommentRaw.id == comment_id).first()
            if not comment:
                raise ValueError(f"Comment {comment_id} not found")
            
            logger.info("Starting comment processing", comment_id=comment_id)
            
            # Check if already processed and not forcing reprocess
            existing_processed = db.query(CommentProcessed).filter(
                CommentProcessed.comment_id == comment.id
            ).first()
            
            if existing_processed and not force_reprocess:
                logger.info("Comment already processed", comment_id=comment_id)
                return {"status": "already_processed", "comment_id": comment_id}
            
            # Step 1: Ingest Tool - PII masking, language detection
            ingest_result = await self._call_ingest_tool(comment.text_raw)
            if not ingest_result:
                return self._create_error_result(comment_id, "ingest_failed")
            
            # Update comment with ingest results
            comment.pii_masked = ingest_result.get("pii_masked", comment.text_raw)
            comment.lang = ingest_result.get("language")
            
            # Step 2: Clause Linking
            clause_result = await self._call_clause_linker(
                comment.pii_masked, str(comment.draft_id)
            )
            clause_guesses = clause_result.get("clause_candidates", []) if clause_result else []
            
            # Create or update processed record
            if existing_processed:
                processed = existing_processed
                processed.text_normalized = ingest_result.get("normalized_text", comment.pii_masked)
                processed.clause_guesses = clause_guesses
            else:
                processed = CommentProcessed(
                    comment_id=comment.id,
                    text_normalized=ingest_result.get("normalized_text", comment.pii_masked),
                    clause_guesses=clause_guesses,
                    embedding=ingest_result.get("embedding")
                )
                db.add(processed)
            
            db.flush()  # Get the processed ID
            
            # Step 3: Classification
            classify_result = await self._call_classify_tool(
                processed.text_normalized, comment.lang
            )
            
            if not classify_result:
                return self._create_error_result(comment_id, "classify_failed")
            
            confidence = classify_result.get("confidence", 0.0)
            
            # Create or update prediction
            existing_prediction = db.query(Prediction).filter(
                Prediction.comment_id == processed.comment_id
            ).first()
            
            prediction_data = {
                "sentiment_label": classify_result.get("sentiment_label"),
                "sentiment_score": classify_result.get("sentiment_score"),
                "sentiment_intensity": classify_result.get("sentiment_intensity"),
                "stance": classify_result.get("stance"),
                "aspects": classify_result.get("aspects", []),
                "confidence": confidence,
                "model_version": classify_result.get("model_version", "unknown"),
                "ci_low": classify_result.get("ci_low"),
                "ci_high": classify_result.get("ci_high")
            }
            
            if existing_prediction:
                for key, value in prediction_data.items():
                    setattr(existing_prediction, key, value)
                prediction = existing_prediction
            else:
                prediction = Prediction(comment_id=processed.comment_id, **prediction_data)
                db.add(prediction)
            
            # Step 4: Quality Check
            if confidence < self.confidence_threshold:
                logger.warning(
                    "Low confidence prediction - queuing for human review",
                    comment_id=comment_id,
                    confidence=confidence
                )
                # TODO: Add to human review queue
                await self._audit_log(db, "comment", comment_id, "low_confidence", {
                    "confidence": confidence,
                    "threshold": self.confidence_threshold
                })
            
            # Step 5: Summarization (if confidence is OK or forced)
            if confidence >= self.confidence_threshold or force_reprocess:
                summary_result = await self._call_summarize_tool(
                    processed.text_normalized,
                    clause_guesses[0] if clause_guesses else None
                )
                
                if summary_result:
                    # Create or update summary
                    existing_summary = db.query(Summary).filter(
                        Summary.comment_id == processed.comment_id
                    ).first()
                    
                    summary_data = {
                        "summary_text": summary_result.get("summary"),
                        "confidence": summary_result.get("confidence", 0.0),
                        "model_version": summary_result.get("model_version", "unknown")
                    }
                    
                    if existing_summary:
                        for key, value in summary_data.items():
                            setattr(existing_summary, key, value)
                    else:
                        summary = Summary(comment_id=processed.comment_id, **summary_data)
                        db.add(summary)
            
            db.commit()
            
            # Step 6 & 7: Deduplication and Keywords (async)
            await self._trigger_post_processing(str(comment.draft_id))
            
            logger.info("Comment processing completed", comment_id=comment_id, confidence=confidence)
            
            return {
                "status": "success",
                "comment_id": comment_id,
                "confidence": confidence,
                "sentiment": classify_result.get("sentiment_label"),
                "stance": classify_result.get("stance"),
                "clauses": clause_guesses
            }
            
        except Exception as e:
            db.rollback()
            logger.error("Comment processing failed", comment_id=comment_id, error=str(e))
            return self._create_error_result(comment_id, "processing_failed", str(e))
        finally:
            db.close()
    
    async def _call_ingest_tool(self, text: str) -> Optional[Dict[str, Any]]:
        """Call the ingest tool for PII masking and normalization"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.tool_urls['ingest']}/process",
                    json={"text": text},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error("Ingest tool call failed", error=str(e))
        return None
    
    async def _call_clause_linker(self, text: str, draft_id: str) -> Optional[Dict[str, Any]]:
        """Call the clause linker tool"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.tool_urls['clause_linker']}/link",
                    json={"text": text, "draft_id": draft_id},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error("Clause linker call failed", error=str(e))
        return None
    
    async def _call_classify_tool(self, text: str, language: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call the classification tool"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.tool_urls['classify']}/classify",
                    json={"text": text, "language": language},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error("Classify tool call failed", error=str(e))
        return None
    
    async def _call_summarize_tool(self, text: str, clause_ref: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call the summarization tool"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.tool_urls['summarize']}/summarize",
                    json={"text": text, "clause_ref": clause_ref},
                    timeout=60.0  # Longer timeout for summarization
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error("Summarize tool call failed", error=str(e))
        return None
    
    async def _trigger_post_processing(self, draft_id: str):
        """Trigger deduplication and keyword extraction for the draft"""
        # These are lower priority and can be done asynchronously
        deduplicate_comments.delay(draft_id)
        extract_keywords.delay(draft_id)
    
    async def _audit_log(self, db: Session, entity: str, entity_id: str, change_type: str, data: Dict[str, Any]):
        """Create audit log entry"""
        audit = Audit(
            entity=entity,
            entity_id=entity_id,
            change_type=change_type,
            change_data=data,
            user_id="system"
        )
        db.add(audit)
    
    def _create_error_result(self, comment_id: str, error_type: str, details: str = "") -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "status": "error",
            "comment_id": comment_id,
            "error_type": error_type,
            "details": details
        }

# Celery tasks
@celery_app.task(bind=True, max_retries=3)
def process_comment_async(self, comment_id: str, force_reprocess: bool = False):
    """Async task to process a comment"""
    try:
        import asyncio
        coordinator = CoordinatorAgent()
        result = asyncio.run(coordinator.process_comment(comment_id, force_reprocess))
        return result
    except Exception as e:
        logger.error("Async comment processing failed", comment_id=comment_id, error=str(e))
        self.retry(countdown=60, exc=e)

@celery_app.task
def deduplicate_comments(draft_id: str):
    """Async task to deduplicate comments for a draft"""
    # TODO: Implement deduplication logic
    logger.info("Deduplication triggered", draft_id=draft_id)
    pass

@celery_app.task
def extract_keywords(draft_id: str):
    """Async task to extract keywords for a draft"""
    # TODO: Implement keyword extraction logic
    logger.info("Keyword extraction triggered", draft_id=draft_id)
    pass
