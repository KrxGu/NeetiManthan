from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import csv
import io
import structlog

from app.core.database import get_db
from app.models import CommentRaw, CommentProcessed, Prediction, Summary
from app.schemas.comment import (
    CommentCreate, CommentResponse, CommentWithAnalysis, 
    CommentBulkUpload, CommentFilter
)
from app.services.coordinator import process_comment_async

logger = structlog.get_logger()
router = APIRouter()

@router.post("/comments", response_model=CommentResponse)
async def create_comment(
    comment: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new comment and trigger processing"""
    try:
        # Create raw comment
        db_comment = CommentRaw(
            draft_id=comment.draft_id,
            text_raw=comment.text_raw,
            user_meta=comment.user_meta or {}
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        
        # Trigger async processing
        background_tasks.add_task(process_comment_async, str(db_comment.id))
        
        logger.info("Comment created", comment_id=str(db_comment.id))
        return db_comment
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to create comment", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")

@router.post("/comments/bulk")
async def upload_comments_bulk(
    bulk_data: CommentBulkUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Upload multiple comments at once"""
    try:
        created_comments = []
        
        for comment_data in bulk_data.comments:
            db_comment = CommentRaw(
                draft_id=bulk_data.draft_id,
                text_raw=comment_data.get("text", ""),
                user_meta=comment_data.get("meta", {})
            )
            db.add(db_comment)
            created_comments.append(db_comment)
        
        db.commit()
        
        # Trigger async processing for all comments
        for comment in created_comments:
            background_tasks.add_task(process_comment_async, str(comment.id))
        
        logger.info("Bulk comments created", count=len(created_comments))
        return {"message": f"Created {len(created_comments)} comments", "ids": [str(c.id) for c in created_comments]}
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to create bulk comments", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create bulk comments: {str(e)}")

@router.post("/comments/upload-csv")
async def upload_comments_csv(
    draft_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload comments from CSV file"""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        csv_reader = csv.DictReader(io.StringIO(text_content))
        created_comments = []
        
        for row in csv_reader:
            if 'text' in row and row['text'].strip():
                db_comment = CommentRaw(
                    draft_id=draft_id,
                    text_raw=row['text'],
                    user_meta={k: v for k, v in row.items() if k != 'text'}
                )
                db.add(db_comment)
                created_comments.append(db_comment)
        
        db.commit()
        
        # Trigger async processing
        for comment in created_comments:
            background_tasks.add_task(process_comment_async, str(comment.id))
        
        logger.info("CSV comments uploaded", count=len(created_comments))
        return {"message": f"Uploaded {len(created_comments)} comments from CSV"}
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded")
    except Exception as e:
        db.rollback()
        logger.error("Failed to upload CSV comments", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to upload CSV: {str(e)}")

@router.get("/comments", response_model=List[CommentWithAnalysis])
async def list_comments(
    draft_id: Optional[UUID] = None,
    sentiment: Optional[str] = None,
    stance: Optional[str] = None,
    clause_ref: Optional[str] = None,
    min_confidence: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List comments with filters"""
    query = db.query(CommentRaw)
    
    if draft_id:
        query = query.filter(CommentRaw.draft_id == draft_id)
    
    comments = query.offset(skip).limit(limit).all()
    
    # Enrich with analysis data
    enriched_comments = []
    for comment in comments:
        comment_data = CommentWithAnalysis.from_orm(comment)
        
        # Get processed data
        processed = db.query(CommentProcessed).filter(
            CommentProcessed.comment_id == comment.id
        ).first()
        
        if processed:
            comment_data.clause_guesses = processed.clause_guesses
            
            # Get predictions
            prediction = db.query(Prediction).filter(
                Prediction.comment_id == processed.comment_id
            ).first()
            if prediction:
                comment_data.predictions = prediction
            
            # Get summaries
            summaries = db.query(Summary).filter(
                Summary.comment_id == processed.comment_id
            ).all()
            comment_data.summaries = summaries
        
        # Apply filters
        if sentiment and (not comment_data.predictions or comment_data.predictions.sentiment_label != sentiment):
            continue
        if stance and (not comment_data.predictions or comment_data.predictions.stance != stance):
            continue
        if clause_ref and (not comment_data.clause_guesses or clause_ref not in comment_data.clause_guesses):
            continue
        if min_confidence and (not comment_data.predictions or comment_data.predictions.confidence < min_confidence):
            continue
        
        enriched_comments.append(comment_data)
    
    return enriched_comments

@router.get("/comments/{comment_id}", response_model=CommentWithAnalysis)
async def get_comment(
    comment_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific comment with analysis"""
    comment = db.query(CommentRaw).filter(CommentRaw.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment_data = CommentWithAnalysis.from_orm(comment)
    
    # Get processed data
    processed = db.query(CommentProcessed).filter(
        CommentProcessed.comment_id == comment.id
    ).first()
    
    if processed:
        comment_data.clause_guesses = processed.clause_guesses
        
        # Get predictions
        prediction = db.query(Prediction).filter(
            Prediction.comment_id == processed.comment_id
        ).first()
        if prediction:
            comment_data.predictions = prediction
        
        # Get summaries
        summaries = db.query(Summary).filter(
            Summary.comment_id == processed.comment_id
        ).all()
        comment_data.summaries = summaries
    
    return comment_data

@router.post("/comments/{comment_id}/reprocess")
async def reprocess_comment(
    comment_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Reprocess a comment (useful after model updates)"""
    comment = db.query(CommentRaw).filter(CommentRaw.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Trigger reprocessing
    background_tasks.add_task(process_comment_async, str(comment_id), force_reprocess=True)
    
    return {"message": "Comment reprocessing triggered"}

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a comment"""
    comment = db.query(CommentRaw).filter(CommentRaw.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(comment)
    db.commit()
    
    logger.info("Comment deleted", comment_id=str(comment_id))
    return {"message": "Comment deleted successfully"}
