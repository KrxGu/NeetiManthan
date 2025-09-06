from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import csv
import io
import structlog

from app.core.database import get_db
from app.models import (
    Draft, CommentRaw, CommentProcessed, Prediction, 
    Summary, Cluster, Keyword
)

logger = structlog.get_logger()
router = APIRouter()

@router.get("/analytics/drafts/{draft_id}/summary")
async def get_draft_summary(
    draft_id: UUID,
    db: Session = Depends(get_db)
):
    """Get analytics summary for a draft"""
    # Verify draft exists
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Get basic counts
    total_comments = db.query(func.count(CommentRaw.id)).filter(
        CommentRaw.draft_id == draft_id
    ).scalar()
    
    processed_comments = db.query(func.count(CommentProcessed.comment_id)).join(
        CommentRaw, CommentProcessed.comment_id == CommentRaw.id
    ).filter(CommentRaw.draft_id == draft_id).scalar()
    
    # Sentiment distribution
    sentiment_dist = db.query(
        Prediction.sentiment_label,
        func.count(Prediction.id).label('count')
    ).join(
        CommentProcessed, Prediction.comment_id == CommentProcessed.comment_id
    ).join(
        CommentRaw, CommentProcessed.comment_id == CommentRaw.id
    ).filter(
        CommentRaw.draft_id == draft_id
    ).group_by(Prediction.sentiment_label).all()
    
    # Stance distribution
    stance_dist = db.query(
        Prediction.stance,
        func.count(Prediction.id).label('count')
    ).join(
        CommentProcessed, Prediction.comment_id == CommentProcessed.comment_id
    ).join(
        CommentRaw, CommentProcessed.comment_id == CommentRaw.id
    ).filter(
        CommentRaw.draft_id == draft_id
    ).group_by(Prediction.stance).all()
    
    # Language distribution
    lang_dist = db.query(
        CommentRaw.lang,
        func.count(CommentRaw.id).label('count')
    ).filter(
        CommentRaw.draft_id == draft_id
    ).group_by(CommentRaw.lang).all()
    
    # Confidence distribution
    avg_confidence = db.query(func.avg(Prediction.confidence)).join(
        CommentProcessed, Prediction.comment_id == CommentProcessed.comment_id
    ).join(
        CommentRaw, CommentProcessed.comment_id == CommentRaw.id
    ).filter(
        CommentRaw.draft_id == draft_id
    ).scalar()
    
    # Cluster count
    cluster_count = db.query(func.count(Cluster.id)).filter(
        Cluster.draft_id == draft_id
    ).scalar()
    
    return {
        "draft_id": str(draft_id),
        "draft_title": draft.title,
        "total_comments": total_comments or 0,
        "processed_comments": processed_comments or 0,
        "processing_rate": (processed_comments / total_comments * 100) if total_comments > 0 else 0,
        "sentiment_distribution": {item.sentiment_label: item.count for item in sentiment_dist},
        "stance_distribution": {item.stance: item.count for item in stance_dist},
        "language_distribution": {item.lang or 'unknown': item.count for item in lang_dist},
        "average_confidence": float(avg_confidence) if avg_confidence else 0,
        "cluster_count": cluster_count or 0
    }

@router.get("/analytics/drafts/{draft_id}/clause-analysis")
async def get_clause_analysis(
    draft_id: UUID,
    db: Session = Depends(get_db)
):
    """Get per-clause analysis"""
    # Verify draft exists
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Get clause-wise comment distribution
    clause_analysis = {}
    
    # Get all processed comments for this draft
    comments = db.query(CommentProcessed).join(
        CommentRaw, CommentProcessed.comment_id == CommentRaw.id
    ).filter(CommentRaw.draft_id == draft_id).all()
    
    for comment in comments:
        if comment.clause_guesses:
            for clause_ref in comment.clause_guesses:
                if clause_ref not in clause_analysis:
                    clause_analysis[clause_ref] = {
                        "total_comments": 0,
                        "sentiment_distribution": {},
                        "stance_distribution": {},
                        "avg_confidence": 0,
                        "confidences": []
                    }
                
                clause_analysis[clause_ref]["total_comments"] += 1
                
                # Get prediction for this comment
                prediction = db.query(Prediction).filter(
                    Prediction.comment_id == comment.comment_id
                ).first()
                
                if prediction:
                    # Sentiment
                    sentiment = prediction.sentiment_label
                    if sentiment:
                        clause_analysis[clause_ref]["sentiment_distribution"][sentiment] = \
                            clause_analysis[clause_ref]["sentiment_distribution"].get(sentiment, 0) + 1
                    
                    # Stance
                    stance = prediction.stance
                    if stance:
                        clause_analysis[clause_ref]["stance_distribution"][stance] = \
                            clause_analysis[clause_ref]["stance_distribution"].get(stance, 0) + 1
                    
                    # Confidence
                    clause_analysis[clause_ref]["confidences"].append(prediction.confidence)
    
    # Calculate average confidences
    for clause_ref in clause_analysis:
        confidences = clause_analysis[clause_ref]["confidences"]
        if confidences:
            clause_analysis[clause_ref]["avg_confidence"] = sum(confidences) / len(confidences)
        del clause_analysis[clause_ref]["confidences"]  # Remove raw data
    
    return clause_analysis

@router.get("/analytics/drafts/{draft_id}/keywords")
async def get_keywords(
    draft_id: UUID,
    facet: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get keywords for a draft"""
    query = db.query(Keyword).filter(Keyword.draft_id == draft_id)
    
    if facet:
        query = query.filter(Keyword.facet == facet)
    
    keywords = query.order_by(Keyword.weight.desc()).limit(limit).all()
    
    return [
        {
            "term": kw.term,
            "weight": kw.weight,
            "frequency": kw.frequency,
            "facet": kw.facet
        }
        for kw in keywords
    ]

@router.get("/analytics/drafts/{draft_id}/clusters")
async def get_clusters(
    draft_id: UUID,
    min_size: int = 2,
    db: Session = Depends(get_db)
):
    """Get comment clusters for deduplication analysis"""
    clusters = db.query(Cluster).filter(
        and_(Cluster.draft_id == draft_id, Cluster.size >= min_size)
    ).order_by(Cluster.size.desc()).all()
    
    cluster_data = []
    for cluster in clusters:
        # Get representative comment
        rep_comment = None
        if cluster.representative_id:
            rep_comment = db.query(CommentRaw).filter(
                CommentRaw.id == cluster.representative_id
            ).first()
        
        cluster_data.append({
            "cluster_id": cluster.cluster_id,
            "size": cluster.size,
            "member_ids": [str(id) for id in cluster.member_ids],
            "representative_text": rep_comment.pii_masked if rep_comment else None
        })
    
    return cluster_data

@router.get("/analytics/drafts/{draft_id}/export")
async def export_draft_analysis(
    draft_id: UUID,
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """Export draft analysis data"""
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    # Get all comments with analysis
    comments_data = []
    
    comments = db.query(CommentRaw).filter(CommentRaw.draft_id == draft_id).all()
    
    for comment in comments:
        row = {
            "comment_id": str(comment.id),
            "text_raw": comment.text_raw,
            "pii_masked": comment.pii_masked,
            "language": comment.lang,
            "created_at": comment.created_at.isoformat(),
        }
        
        # Get processed data
        processed = db.query(CommentProcessed).filter(
            CommentProcessed.comment_id == comment.id
        ).first()
        
        if processed:
            row["clause_guesses"] = ",".join(processed.clause_guesses) if processed.clause_guesses else ""
            
            # Get prediction
            prediction = db.query(Prediction).filter(
                Prediction.comment_id == processed.comment_id
            ).first()
            
            if prediction:
                row.update({
                    "sentiment_label": prediction.sentiment_label,
                    "sentiment_score": prediction.sentiment_score,
                    "stance": prediction.stance,
                    "aspects": ",".join(prediction.aspects) if prediction.aspects else "",
                    "confidence": prediction.confidence,
                    "model_version": prediction.model_version
                })
            
            # Get summary
            summary = db.query(Summary).filter(
                Summary.comment_id == processed.comment_id
            ).first()
            
            if summary:
                row["summary"] = summary.summary_text
                row["summary_confidence"] = summary.confidence
        
        comments_data.append(row)
    
    if format == "csv":
        output = io.StringIO()
        if comments_data:
            writer = csv.DictWriter(output, fieldnames=comments_data[0].keys())
            writer.writeheader()
            writer.writerows(comments_data)
        
        response = Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=draft_{draft_id}_analysis.csv"}
        )
        return response
    
    else:  # JSON
        return {
            "draft_id": str(draft_id),
            "exported_at": datetime.utcnow().isoformat(),
            "comments": comments_data
        }
