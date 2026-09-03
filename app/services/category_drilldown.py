"""Orchestration service for category drill-down analysis."""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.models import Report, Cluster
from app.ml.subcategory_clustering import run_subcategory_clustering
from app.ml.subcategory_visualization import plot_subcategory_risk, plot_subcategory_embeddings_pca
from app.ml.visualization_common import ensure_drilldown_output_dir


def execute_category_drilldown(
    db: Session,
    category_input: str,
    generate_plots: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Perform hierarchical drill-down into a specific top-level category."""
    start_time = time.perf_counter()

    # 1. Dataset Scope Check
    total_dataset_records = db.query(Report).count()
    if total_dataset_records == 0:
        return {
            "status": "error",
            "message": "No active dataset found in database. Please run 'python -m app.cli.run_pipeline' first."
        }

    # 2. Category Resolution
    clusters = db.query(Cluster).filter(Cluster.cluster_num != -1).order_by(Cluster.report_count.desc()).all()
    matched_cluster = _resolve_category(category_input, clusters)

    if not matched_cluster:
        available = [(c.label, c.report_count) for c in clusters]
        return {
            "status": "category_not_found",
            "requested": category_input,
            "available": available
        }

    # 3. Retrieve category reports & pre-computed embeddings
    reports = db.query(Report).filter(Report.cluster_id == matched_cluster.id).all()
    if not reports:
        # Fallback query if cluster_id is null
        reports = db.query(Report).all()
        reports = [r for r in reports if matched_cluster.label.lower() in (r.extracted_info or "").lower()]

    if not reports:
        return {
            "status": "error",
            "message": f"Category '{matched_cluster.label}' contains zero records in the current dataset scope."
        }

    # Extract vectors and report dicts
    vectors_list = []
    rep_dicts = []
    for r in reports:
        if not r.embedding:
            continue
        try:
            vec = np.asarray(json.loads(r.embedding), dtype=np.float32)
            if vec.shape == (384,):
                vectors_list.append(vec)
                ext = json.loads(r.extracted_info) if r.extracted_info else {}
                sev = json.loads(r.severity_info) if r.severity_info else {}
                rep_dicts.append({
                    "id": r.id,
                    "description": r.description,
                    "event": r.event,
                    "employer": r.employer,
                    "state": r.state,
                    "industry": r.industry,
                    "extracted_info": ext,
                    "severity_info": sev,
                    "timestamp": r.timestamp
                })
        except Exception:
            continue

    if not vectors_list:
        return {
            "status": "error",
            "message": f"No valid embeddings found for category '{matched_cluster.label}'."
        }

    vectors = np.vstack(vectors_list)

    # 4. Subcategory Clustering
    sub_results = run_subcategory_clustering(vectors, rep_dicts)

    # 5. Visualizations
    plot_files = {}
    if generate_plots:
        out_path = Path(output_dir) if output_dir else ensure_drilldown_output_dir()
        
        risk_plot = plot_subcategory_risk(matched_cluster.label, sub_results["subcategories"], sub_results["noise_count"], out_path)
        emb_plot = plot_subcategory_embeddings_pca(
            matched_cluster.label, sub_results["subcategories"], vectors, sub_results["labels"], out_path
        )
        
        if risk_plot:
            plot_files["subcategory_risk"] = str(risk_plot)
        if emb_plot:
            plot_files["subcategory_embeddings"] = str(emb_plot)

    proc_time = time.perf_counter() - start_time

    return {
        "status": "success",
        "category": matched_cluster.label,
        "total_dataset_records": total_dataset_records,
        "category_records": len(rep_dicts),
        "category_percentage": round((len(rep_dicts) / total_dataset_records) * 100.0, 1),
        "subcategories": sub_results["subcategories"],
        "noise_count": sub_results["noise_count"],
        "noise_percentage": sub_results["noise_percentage"],
        "processing_time": round(proc_time, 2),
        "plot_files": plot_files
    }


def _resolve_category(input_str: str, clusters: List[Cluster]) -> Optional[Cluster]:
    """Resolve user input string to canonical Cluster object case-insensitively."""
    if not input_str or not clusters:
        return None

    clean_in = input_str.strip().lower()
    
    # 1. Exact match
    for c in clusters:
        if c.label.lower() == clean_in:
            return c

    # 2. Direct prefix/keyword mapping shortcuts
    mappings = {
        "fall": "Falls / Working at Height",
        "falls": "Falls / Working at Height",
        "height": "Falls / Working at Height",
        "vehicle": "Vehicle / Struck-by",
        "struck": "Vehicle / Struck-by",
        "truck": "Truck Related Incidents",
        "electric": "Electrical Exposure",
        "electrical": "Electrical Exposure",
        "chemical": "Chemical Exposure",
        "confined": "Confined Space",
        "loto": "Equipment Isolation / LOTO",
        "isolation": "Equipment Isolation / LOTO",
        "lifting": "Lifting / Material Handling",
        "material": "Lifting / Material Handling",
        "fire": "Fire / Ignition",
        "ignition": "Fire / Ignition",
        "pressure": "Pressure / Stored Energy",
        "stored energy": "Pressure / Stored Energy",
        "press": "Press Related Incidents",
        "saw": "Saw Related Incidents",
        "line": "Line Related Incidents",
    }
    
    mapped_name = mappings.get(clean_in)
    if mapped_name:
        for c in clusters:
            if c.label.lower() == mapped_name.lower():
                return c

    # 3. Partial substring match
    for c in clusters:
        if clean_in in c.label.lower():
            return c

    return None
