from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import httpx
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        result = db.execute(text("SELECT 1"))
        status["services"]["database"] = "healthy"
    except Exception as e:
        status["services"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
    
    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        status["services"]["redis"] = "healthy"
    except Exception as e:
        status["services"]["redis"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
    
    # Check tool services
    tool_services = [
        ("ingest-tool", settings.ingest_tool_url),
        ("classify-tool", settings.classify_tool_url),
        ("clause-linker", settings.clause_linker_url),
    ]
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in tool_services:
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                if response.status_code == 200:
                    status["services"][service_name] = "healthy"
                else:
                    status["services"][service_name] = f"unhealthy: HTTP {response.status_code}"
                    status["status"] = "degraded"
            except Exception as e:
                status["services"][service_name] = f"unhealthy: {str(e)}"
                status["status"] = "degraded"
    
    if status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=status)
    
    return status

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check for Kubernetes"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail={"status": "not ready", "error": str(e)})

@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"}
