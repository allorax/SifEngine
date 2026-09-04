import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import numpy as np
from sklearn.decomposition import PCA

from app.database import get_db
from app.models import Cluster, Report, RiskScore, Forecast
from app.schemas import ClusterResponse, ReportResponse, RiskScoreResponse, ForecastResponse
from app.services.category_drilldown import execute_category_drilldown

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("", response_model=List[ClusterResponse])
def get_clusters(db: Session = Depends(get_db)):
    """List all discovered safety hazard clusters."""
    clusters = db.query(Cluster).order_by(Cluster.report_count.desc()).all()
    return clusters


@router.get("/3d-embeddings")
def get_3d_embeddings(max_points: int = Query(2500, ge=100, le=5000), db: Session = Depends(get_db)):
    """Compute 3D PCA coordinates for report embeddings for WebGL 3D point cloud visualization."""
    clusters_db = db.query(Cluster).all()
    cluster_info = {c.id: {"label": c.label, "cluster_num": c.cluster_num} for c in clusters_db}
    
    risk_db = db.query(RiskScore).all()
    risk_scores = {r.cluster_id: r.risk_score for r in risk_db}

    reports = db.query(
        Report.id, Report.cluster_id, Report.employer, Report.state, Report.event, Report.description, Report.embedding
    ).filter(Report.embedding.isnot(None)).limit(max_points).all()
    
    vectors = []
    metadata = []
    
    for r in reports:
        if not r.embedding:
            continue
        try:
            vec = np.asarray(json.loads(r.embedding), dtype=np.float32)
            if vec.shape == (384,) and np.isfinite(vec).all():
                c_id = r.cluster_id
                c_label = cluster_info.get(c_id, {}).get("label", "Unclustered / Outlier") if c_id else "Unclustered / Outlier"
                risk_val = risk_scores.get(c_id, 0.0) if c_id else 0.0
                
                vectors.append(vec)
                metadata.append({
                    "id": r.id,
                    "cluster_id": c_id if c_id is not None else -1,
                    "cluster_label": c_label,
                    "employer": r.employer or "Unknown Employer",
                    "state": r.state or "N/A",
                    "event": r.event or "Safety Incident",
                    "risk_score": risk_val,
                    "description": r.description[:180] + "..." if len(r.description) > 180 else r.description
                })
        except Exception:
            continue

    if not vectors:
        return {"points": [], "centroids": [], "total_points": 0}

    matrix = np.vstack(vectors)
    pca = PCA(n_components=3, random_state=42)
    coords_3d = pca.fit_transform(matrix)

    # Scale coordinates to fit nicely in 3D space ([-15, 15])
    std_dev = np.std(coords_3d, axis=0)
    std_dev[std_dev == 0] = 1.0
    coords_scaled = (coords_3d / std_dev) * 10.0

    points = []
    cluster_points_map = {}

    for i, meta in enumerate(metadata):
        pt = {
            **meta,
            "x": float(round(coords_scaled[i, 0], 3)),
            "y": float(round(coords_scaled[i, 1], 3)),
            "z": float(round(coords_scaled[i, 2], 3))
        }
        points.append(pt)
        c_id = meta["cluster_id"]
        if c_id not in cluster_points_map:
            cluster_points_map[c_id] = []
        cluster_points_map[c_id].append([pt["x"], pt["y"], pt["z"]])

    centroids = []
    for c in clusters_db:
        if c.id in cluster_points_map and len(cluster_points_map[c.id]) > 0:
            arr = np.array(cluster_points_map[c.id])
            centroid_coord = np.mean(arr, axis=0).tolist()
            centroids.append({
                "cluster_id": c.id,
                "cluster_label": c.label,
                "report_count": c.report_count,
                "risk_score": risk_scores.get(c.id, 0.0),
                "centroid": [round(v, 3) for v in centroid_coord]
            })

    return {
        "total_points": len(points),
        "explained_variance": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "points": points,
        "centroids": centroids
    }


@router.get("/drilldown")
def get_category_drilldown(category: str, db: Session = Depends(get_db)):
    """Perform category drilldown into subcategories and return structured risk metrics."""
    result = execute_category_drilldown(db, category, generate_plots=False)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Drilldown failed"))
    if result.get("status") == "category_not_found":
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")
    
    # Enhance subcategories with sample reports
    matched_cluster = db.query(Cluster).filter(Cluster.label == result.get("category")).first()
    if matched_cluster:
        all_cluster_reports = db.query(Report).filter(Report.cluster_id == matched_cluster.id).limit(100).all()
        report_list = []
        for r in all_cluster_reports:
            report_list.append({
                "id": r.id,
                "employer": r.employer or "Unknown",
                "state": r.state or "N/A",
                "event": r.event or "Safety Incident",
                "description": r.description[:200] + "..." if len(r.description) > 200 else r.description
            })
        
        # Attach sample reports per subcategory
        for sub in result.get("subcategories", []):
            indices = sub.get("indices", [])
            sample_reps = []
            for idx in indices[:5]:
                if idx < len(report_list):
                    sample_reps.append(report_list[idx])
            sub["sample_reports"] = sample_reps
            if "indices" in sub:
                del sub["indices"]

    return result


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

