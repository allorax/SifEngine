import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import ReportResponse, SimilarReportsResponse
from app.ml.embeddings import deserialize_vector
from app.ml.similarity import find_top_similar_reports

router = APIRouter(prefix="/reports", tags=["Reports"])


def format_report_response(r: Report) -> dict:
    return {
        "id": r.id,
        "source_dataset": r.source_dataset,
        "source_record_id": r.source_record_id,
        "timestamp": r.timestamp,
        "description": r.description,
        "employer": r.employer,
        "location": r.location,
        "state": r.state,
        "industry": r.industry,
        "event": r.event,
        "source": r.source,
        "severity_info": json.loads(r.severity_info) if r.severity_info else None,
        "extracted_info": json.loads(r.extracted_info) if r.extracted_info else None,
        "cluster_id": r.cluster_id
    }


@router.get("", response_model=List[ReportResponse])
def get_reports(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve paginated reports, optionally filtered by state."""
    query = db.query(Report)
    if state:
        query = query.filter(Report.state == state.upper())
    reports = query.offset(offset).limit(limit).all()
    return [format_report_response(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    """Retrieve a single report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report #{report_id} not found.")
    return format_report_response(report)


@router.get("/{report_id}/similar", response_model=SimilarReportsResponse)
def get_similar_reports(
    report_id: int,
    top_n: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Find top N semantically similar reports using vector cosine similarity."""
    target_report = db.query(Report).filter(Report.id == report_id).first()
    if not target_report:
        raise HTTPException(status_code=404, detail=f"Report #{report_id} not found.")

    target_vec = deserialize_vector(target_report.embedding)

    # Load all stored reports for similarity lookup
    all_db_reports = db.query(Report.id, Report.description, Report.employer, Report.timestamp, Report.severity_info, Report.embedding).all()

    all_reports = []
    for r in all_db_reports:
        all_reports.append({
            "id": r.id,
            "description": r.description,
            "employer": r.employer,
            "timestamp": r.timestamp,
            "severity_info": json.loads(r.severity_info) if r.severity_info else {},
            "vector": deserialize_vector(r.embedding)
        })

    similar_items = find_top_similar_reports(report_id, target_vec, all_reports, top_n=top_n)

    return {
        "report_id": report_id,
        "similar_reports": similar_items
    }
