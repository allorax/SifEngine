from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pipeline import execute_pipeline

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post("/run")
def trigger_pipeline_run(limit: Optional[int] = Query(5000, ge=1), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Trigger execution of the end-to-end OSHA processing pipeline."""
    result = execute_pipeline(db, limit=limit)
    return result
