import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cluster, Report, RiskScore, Forecast
from app.schemas import ClusterResponse, ReportResponse, RiskScoreResponse, ForecastResponse

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("", response_model=List[ClusterResponse])
def get_clusters(db: Session = Depends(get_db)):
    """List all discovered safety hazard clusters."""
    clusters = db.query(Cluster).order_by(Cluster.report_count.desc()).all()
    return clusters


@router.get("/{cluster_id}", response_model=ClusterResponse)
def get_cluster_by_id(cluster_id: int, db: Session = Depends(get_db)):
    """Retrieve cluster details by ID."""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster #{cluster_id} not found.")
    return cluster


@router.get("/{cluster_id}/reports", response_model=List[ReportResponse])
def get_cluster_reports(
    cluster_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve reports assigned to a specific cluster."""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster #{cluster_id} not found.")

    reports = db.query(Report).filter(Report.cluster_id == cluster_id).offset(offset).limit(limit).all()
    result = []
    for r in reports:
        result.append({
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
        })
    return result


@router.get("/{cluster_id}/risk", response_model=RiskScoreResponse)
def get_cluster_risk_score(cluster_id: int, db: Session = Depends(get_db)):
    """Retrieve 5-factor explainable risk score for a cluster."""
    risk = db.query(RiskScore).filter(RiskScore.cluster_id == cluster_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk score for cluster #{cluster_id} not found.")
    return {
        "cluster_id": risk.cluster_id,
        "risk_score": risk.risk_score,
        "frequency": risk.frequency,
        "near_miss_intensity": risk.near_miss_intensity,
        "severity": risk.severity,
        "trend": risk.trend,
        "recency": risk.recency
    }


@router.get("/{cluster_id}/forecast", response_model=ForecastResponse)
def get_cluster_forecast(cluster_id: int, db: Session = Depends(get_db)):
    """Retrieve trend trajectory classification and monthly count forecast for a cluster."""
    forecast = db.query(Forecast).filter(Forecast.cluster_id == cluster_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail=f"Forecast for cluster #{cluster_id} not found.")
    
    return {
        "cluster_id": forecast.cluster_id,
        "trend": forecast.trend_classification,
        "forecast": json.loads(forecast.forecast_json)
    }
