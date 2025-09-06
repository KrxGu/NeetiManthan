from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import structlog

from app.core.database import get_db
from app.models import Draft, Clause
from app.services.draft_processor import DraftProcessor
from app.schemas.draft import DraftCreate, DraftResponse, ClauseResponse

logger = structlog.get_logger()
router = APIRouter()

@router.post("/drafts", response_model=DraftResponse)
async def create_draft(
    draft: DraftCreate,
    db: Session = Depends(get_db)
):
    """Create a new draft law document"""
    try:
        # Create draft record
        db_draft = Draft(
            title=draft.title,
            content=draft.content,
            text_uri=draft.text_uri
        )
        db.add(db_draft)
        db.flush()  # Get the ID
        
        # Process draft to extract clauses
        processor = DraftProcessor()
        clauses = await processor.extract_clauses(draft.content, db_draft.id)
        
        # Save clauses
        for clause_data in clauses:
            clause = Clause(
                draft_id=db_draft.id,
                ref=clause_data["ref"],
                text=clause_data["text"],
                embedding=clause_data["embedding"]
            )
            db.add(clause)
        
        db.commit()
        db.refresh(db_draft)
        
        logger.info("Draft created", draft_id=str(db_draft.id), clauses_count=len(clauses))
        return db_draft
        
    except Exception as e:
        db.rollback()
        logger.error("Failed to create draft", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")

@router.get("/drafts", response_model=List[DraftResponse])
async def list_drafts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all draft documents"""
    drafts = db.query(Draft).offset(skip).limit(limit).all()
    return drafts

@router.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific draft document"""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@router.get("/drafts/{draft_id}/clauses", response_model=List[ClauseResponse])
async def get_draft_clauses(
    draft_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all clauses for a draft"""
    # Verify draft exists
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    clauses = db.query(Clause).filter(Clause.draft_id == draft_id).all()
    return clauses

@router.post("/drafts/upload")
async def upload_draft_file(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload a draft document file"""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        draft_title = title or file.filename or "Uploaded Draft"
        
        # Create draft
        draft_data = DraftCreate(
            title=draft_title,
            content=text_content
        )
        
        return await create_draft(draft_data, db)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        logger.error("Failed to upload draft", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to upload draft: {str(e)}")

@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a draft document"""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    db.delete(draft)
    db.commit()
    
    logger.info("Draft deleted", draft_id=str(draft_id))
    return {"message": "Draft deleted successfully"}
