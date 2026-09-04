import json
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Report, Cluster, RiskScore, Forecast
from app.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Retrieve overview metrics and top risk/emerging clusters for dashboard display."""
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    total_clusters = db.query(func.count(Cluster.id)).filter(Cluster.cluster_num != -1).scalar() or 0

    # Top risk clusters
    top_risk_rows = db.query(Cluster, RiskScore).join(RiskScore, Cluster.id == RiskScore.cluster_id).filter(Cluster.cluster_num != -1).order_by(RiskScore.risk_score.desc()).limit(5).all()

    top_risk_clusters = []
    for c, r in top_risk_rows:
        top_risk_clusters.append({
            "cluster_id": c.id,
            "cluster_num": c.cluster_num,
            "label": c.label,
            "report_count": c.report_count,
            "risk_score": r.risk_score
        })

    # Emerging and Increasing clusters
    forecast_rows = db.query(Cluster, Forecast, RiskScore).join(Forecast, Cluster.id == Forecast.cluster_id).join(RiskScore, Cluster.id == RiskScore.cluster_id).filter(Cluster.cluster_num != -1).all()

    emerging_clusters = []
    increasing_clusters = []

    for c, f, r in forecast_rows:
        entry = {
            "cluster_id": c.id,
            "cluster_num": c.cluster_num,
            "label": c.label,
            "report_count": c.report_count,
            "risk_score": r.risk_score,
            "trend": f.trend_classification
        }
        if f.trend_classification == "Emerging":
            emerging_clusters.append(entry)
        elif f.trend_classification == "Increasing":
            increasing_clusters.append(entry)

    # Recent activity reports
    recent_reports_db = db.query(Report).order_by(Report.timestamp.desc()).limit(5).all()
    recent_activity = []
    for rep in recent_reports_db:
        recent_activity.append({
            "id": rep.id,
            "timestamp": rep.timestamp,
            "employer": rep.employer,
            "state": rep.state,
            "description": rep.description[:150] + "..." if len(rep.description) > 150 else rep.description
        })

    return {
        "total_reports": total_reports,
        "total_clusters": total_clusters,
        "top_risk_clusters": top_risk_clusters,
        "emerging_clusters": emerging_clusters,
        "increasing_clusters": increasing_clusters,
        "recent_activity": recent_activity
    }


@router.get("/forecasts")
def get_all_forecasts(db: Session = Depends(get_db)):
    """Retrieve monthly forecast time-series data for all hazard clusters."""
    rows = db.query(Cluster, Forecast, RiskScore).join(
        Forecast, Cluster.id == Forecast.cluster_id
    ).join(
        RiskScore, Cluster.id == RiskScore.cluster_id
    ).filter(Cluster.cluster_num != -1).all()

    result = []
    for c, f, r in rows:
        forecast_data = json.loads(f.forecast_json) if f.forecast_json else []
        result.append({
            "cluster_id": c.id,
            "cluster_num": c.cluster_num,
            "label": c.label,
            "report_count": c.report_count,
            "risk_score": r.risk_score,
            "trend": f.trend_classification,
            "forecast": forecast_data
        })
    return result


@router.get("/risk-overview")
def get_risk_overview(db: Session = Depends(get_db)):
    """Retrieve complete 5-factor risk score breakdown for all active clusters."""
    rows = db.query(Cluster, RiskScore).join(
        RiskScore, Cluster.id == RiskScore.cluster_id
    ).filter(Cluster.cluster_num != -1).order_by(RiskScore.risk_score.desc()).all()

    result = []
    for c, r in rows:
        result.append({
            "cluster_id": c.id,
            "cluster_num": c.cluster_num,
            "label": c.label,
            "report_count": c.report_count,
            "risk_score": r.risk_score,
            "frequency": r.frequency,
            "near_miss_intensity": r.near_miss_intensity,
            "severity": r.severity,
            "trend": r.trend,
            "recency": r.recency
        })
    return result

