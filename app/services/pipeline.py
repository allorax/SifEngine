import json
import time
from typing import Dict, Any, List
import numpy as np
from sqlalchemy import insert
from sqlalchemy.orm import Session
from app.ml.visualization import generate_all_diagnostics
from app.config import BATCH_SIZE, EMBEDDING_MODEL_NAME
from app.database import init_database
from app.models import Report, Cluster, RiskScore, Forecast
from app.data.loader import load_all_osha_records
from app.data.cleaner import clean_records
from app.nlp.extractors import extract_safety_info_batch
from app.ml.embeddings_optimized import generate_embeddings_optimized, serialize_vector
from app.ml.clustering import run_hdbscan_clustering, calculate_cluster_stats
from app.ml.labeling import generate_cluster_label, deduplicate_cluster_labels
from app.ml.risk import calculate_cluster_risk_score
from app.ml.trend import aggregate_monthly_counts, classify_trend
from app.ml.forecast import generate_cluster_forecast
from app.ml.visualization_common import clear_drilldown_output_dir


def execute_pipeline(
    db: Session,
    limit: int = None,
    generate_plots: bool = True,
    batch_size: int = None,
    representative_sample: bool = True,
) -> Dict[str, Any]:
    """Execute end-to-end OSHA data processing, NLP, embedding, clustering, risk scoring & forecasting pipeline.

    Args:
        db: SQLAlchemy session
        limit: Max records to process (None = all)
        generate_plots: Whether to generate diagnostic visualizations
        batch_size: Batch size for embedding generation (None uses config default)
        representative_sample: Randomly sample limited runs across the source data
    """
    if batch_size is None:
        batch_size = BATCH_SIZE
    start_time = time.perf_counter()
    timing = {}

    init_database()
    clear_drilldown_output_dir()

    # 1. Load raw records
    load_start = time.perf_counter()
    raw_records = load_all_osha_records(
        limit=limit,
        representative_sample=representative_sample and limit is not None,
    )
    timing['load'] = round(time.perf_counter() - load_start, 2)

    # 2. Clean data
    clean_start = time.perf_counter()
    cleaned_records, profile_summary = clean_records(raw_records)
    timing['clean'] = round(time.perf_counter() - clean_start, 2)

    if not cleaned_records:
        return {"status": "error", "message": "No valid records found in OSHA data."}

    # Generate embeddings before refresh so the existing report rows can serve
    # as a cache. The refresh below then replaces stale reports rather than
    # appending duplicates on every pipeline run.
    descriptions = [r["description"] for r in cleaned_records]

    emb_start = time.perf_counter()
    vectors, embedding_stats = generate_embeddings_optimized(db, descriptions, batch_size=batch_size, show_progress=True)
    timing['embeddings'] = embedding_stats['embedding_time_sec']

    # Clear previous analysis and report rows in dependency order. Reports are
    # rebuilt from the selected input, so API totals always reflect this run.
    db.query(Forecast).delete()
    db.query(RiskScore).delete()
    db.query(Cluster).delete()
    db.query(Report).delete()
    db.commit()

    # 3. Process NLP extractions and persist the refreshed reports.
    nlp_start = time.perf_counter()
    nlp_data = extract_safety_info_batch(descriptions, batch_size=batch_size)
    timing['nlp'] = round(time.perf_counter() - nlp_start, 2)

    print(f"\n[EMBEDDING STATS]")
    print(f"  Total texts: {embedding_stats['total_texts']:,}")
    print(f"  Unique texts: {embedding_stats['unique_texts']:,}")
    print(f"  Existing embeddings: {embedding_stats['existing_embeddings']:,}")
    print(f"  New embeddings: {embedding_stats['new_embeddings_required']:,}")
    print(f"  Reused embeddings: {embedding_stats['reused_embeddings']:,}")
    print(f"  Deduplication ratio: {embedding_stats['deduplication_ratio']:.1f}%")
    print(f"  Device: {embedding_stats['device']} ({embedding_stats['device_name']})")
    print(f"  Embedding time: {embedding_stats['embedding_time_sec']:.2f}s")

    report_mappings = []
    for i, r in enumerate(cleaned_records):
        ext_info = nlp_data[i]
        vec_json = serialize_vector(vectors[i])
        report_mappings.append({
            "source_dataset": r["source_dataset"],
            "source_record_id": r["source_record_id"],
            "timestamp": r["timestamp"],
            "description": r["description"],
            "employer": r.get("employer"),
            "location": r.get("location"),
            "state": r.get("state"),
            "industry": r.get("industry"),
            "event": r.get("event"),
            "source": r.get("source"),
            "severity_info": json.dumps(r.get("severity_info", {})),
            "extracted_info": json.dumps(ext_info),
            "raw_data": json.dumps(r.get("raw_data", {})),
            "embedding": vec_json,
            "embedding_model": EMBEDDING_MODEL_NAME,
        })

    # Bulk INSERT with ordered returned IDs avoids one ORM refresh per report.
    report_ids = list(db.scalars(
        insert(Report).returning(Report.id, sort_by_parameter_order=True), report_mappings
    ))
    if len(report_ids) != len(cleaned_records):
        raise RuntimeError("Report persistence returned an unexpected number of IDs.")
    db.commit()

    # 4. HDBSCAN Clustering
    analysis_start = time.perf_counter()
    cluster_labels = run_hdbscan_clustering(vectors)

    # Group reports by cluster label (use IDs instead of objects to avoid session issues)
    cluster_groups = {}
    for idx, label_num in enumerate(cluster_labels):
        cluster_groups.setdefault(int(label_num), []).append(report_ids[idx])

    unique_cluster_nums = [c_num for c_num in cluster_groups.keys() if c_num != -1]
    noise_count = len(cluster_groups.get(-1, []))
    noise_percentage = round((noise_count / len(report_ids)) * 100.0, 2) if report_ids else 0.0

    max_cluster_size = max([len(grp) for cnum, grp in cluster_groups.items() if cnum != -1], default=1)

    discovered_clusters_summary = []
    highest_risk_clusters = []
    increasing_clusters = []
    emerging_clusters = []

    # 5. Pre-compute report dicts for each HDBSCAN cluster
    print(f"\n[DEBUG] Starting HDBSCAN cluster evaluation ({len(unique_cluster_nums)} raw clusters)")
    
    # Map HDBSCAN clusters to general category labels and consolidate micro-clusters sharing the same category
    consolidated_groups: Dict[str, Dict[str, Any]] = {}
    for c_num, rep_ids in cluster_groups.items():
        if c_num == -1:
            continue
        report_indices = [index for index, label in enumerate(cluster_labels) if int(label) == c_num]
        rep_dicts = [{
            "id": report_ids[index],
            "timestamp": cleaned_records[index]["timestamp"],
            "description": cleaned_records[index]["description"],
            "employer": cleaned_records[index].get("employer"),
            "state": cleaned_records[index].get("state"),
            "industry": cleaned_records[index].get("industry"),
            "event": cleaned_records[index].get("event"),
            "severity_info": cleaned_records[index].get("severity_info", {}),
            "extracted_info": nlp_data[index],
        } for index in report_indices]

        # Determine general category label for this micro-cluster
        cat_label = generate_cluster_label(c_num, rep_dicts)
        if cat_label not in consolidated_groups:
            consolidated_groups[cat_label] = {"rep_ids": [], "rep_dicts": []}
        consolidated_groups[cat_label]["rep_ids"].extend(rep_ids)
        consolidated_groups[cat_label]["rep_dicts"].extend(rep_dicts)

    print(f"[DEBUG] Consolidated {len(unique_cluster_nums)} raw clusters into {len(consolidated_groups)} unique general category clusters")

    # Max cluster size among consolidated clusters
    max_cluster_size = max([len(g["rep_ids"]) for g in consolidated_groups.values()], default=1)

    # 5b. Build Cluster models, Risk scores, Trends, and Forecasts for consolidated categories
    for c_idx, (c_label, group_data) in enumerate(consolidated_groups.items()):
        c_num = c_idx + 1
        rep_ids = group_data["rep_ids"]
        rep_dicts = group_data["rep_dicts"]

        c_stats = calculate_cluster_stats(c_num, rep_dicts, len(report_ids))

        cluster_obj = Cluster(
            cluster_num=c_num,
            label=c_label,
            report_count=c_stats["report_count"],
            percentage=c_stats["percentage"],
            dominant_event=c_stats["dominant_event"],
            dominant_hazard=c_stats["dominant_hazard"],
            dominant_industry=c_stats["dominant_industry"],
            dominant_state=c_stats["dominant_state"],
            min_date=c_stats["min_date"],
            max_date=c_stats["max_date"]
        )
        db.add(cluster_obj)
        db.flush()

        # Update reports' cluster_id foreign key using direct SQL to avoid session issues
        db.query(Report).filter(Report.id.in_(rep_ids)).update({"cluster_id": cluster_obj.id}, synchronize_session=False)

        # Monthly Trend
        monthly_data = aggregate_monthly_counts(rep_dicts)
        trend_class, trend_ratio = classify_trend(monthly_data)

        # Risk Score
        risk_dict = calculate_cluster_risk_score(rep_dicts, max_cluster_size, recent_trend_ratio=trend_ratio)
        risk_obj = RiskScore(
            cluster_id=cluster_obj.id,
            risk_score=risk_dict["risk_score"],
            frequency=risk_dict["frequency"],
            near_miss_intensity=risk_dict["near_miss_intensity"],
            severity=risk_dict["severity"],
            trend=risk_dict["trend"],
            recency=risk_dict["recency"]
        )
        db.add(risk_obj)

        # A one- or two-month series only repeats the latest baseline; it is not
        # enough history for a useful activity trajectory or forecast.
        if len(monthly_data) >= 6:
            forecast_list = generate_cluster_forecast(monthly_data)
            db.add(Forecast(
                cluster_id=cluster_obj.id,
                trend_classification=trend_class,
                forecast_json=json.dumps(forecast_list),
            ))
        summary_entry = {
            "cluster_id": cluster_obj.id,
            "cluster_num": c_num,
            "label": c_label,
            "report_count": cluster_obj.report_count,
            "risk_score": risk_dict["risk_score"],
            "trend": trend_class
        }
        discovered_clusters_summary.append(summary_entry)

        highest_risk_clusters.append(summary_entry)
        if trend_class == "Increasing":
            increasing_clusters.append(summary_entry)
        elif trend_class == "Emerging":
            emerging_clusters.append(summary_entry)

    print(f"[DEBUG] Cluster consolidation completed. Created {len(discovered_clusters_summary)} category clusters")

    highest_risk_clusters.sort(key=lambda x: x["risk_score"], reverse=True)

    timing['clustering'] = round(time.perf_counter() - analysis_start, 2)

    # Final explicit commit to ensure all data is persisted
    persist_start = time.perf_counter()
    db.commit()
    timing['persistence'] = round(time.perf_counter() - persist_start, 2)

    # Generate visualizations if requested
    viz_start = time.perf_counter()
    plot_files = {}
    if generate_plots:
        print("\n[GENERATING VISUALIZATIONS]")
        plot_files = generate_all_diagnostics(db)
        for plot_name, plot_path in plot_files.items():
            if plot_path:
                print(f"  ✓ {plot_name}: {plot_path}")
    timing['visualization'] = round(time.perf_counter() - viz_start, 2)

    # Verify final data
    final_reports = db.query(Report).count()
    final_clusters = db.query(Cluster).filter(Cluster.cluster_num != -1).count()

    print(f"\n[HDBSCAN OUTPUT]")
    print(f"  Total points: {final_reports:,}")
    print(f"  Clusters found: {final_clusters}")
    print(f"  Noise points: {noise_count:,}")
    print(f"  Noise ratio: {noise_percentage:.1f}%")

    # Print timing summary
    total_time = time.perf_counter() - start_time
    timing['total'] = round(total_time, 2)

    print(f"\n[PIPELINE TIMING]")
    print(f"  Load:          {timing.get('load', 0):6.2f}s")
    print(f"  Clean:         {timing.get('clean', 0):6.2f}s")
    print(f"  NLP:           {timing.get('nlp', 0):6.2f}s")
    print(f"  Embeddings:    {timing.get('embeddings', 0):6.2f}s")
    print(f"  Clustering:    {timing.get('clustering', 0):6.2f}s")
    print(f"  Risk/Trend:    {timing.get('risk', 0):6.2f}s")
    print(f"  Persistence:   {timing.get('persistence', 0):6.2f}s")
    print(f"  Visualization: {timing.get('visualization', 0):6.2f}s")
    print(f"  {'─' * 30}")
    print(f"  TOTAL:         {timing['total']:6.2f}s")

    return {
        "status": "success",
        "processing_time_seconds": timing['total'],
        "timing_breakdown": timing,
        "profile_summary": profile_summary,
        "total_records_processed": len(cleaned_records),
        "embedding_stats": embedding_stats,
        "clusters_discovered": len(unique_cluster_nums),
        "noise_percentage": noise_percentage,
        "highest_risk_clusters": highest_risk_clusters[:5],
        "increasing_clusters": increasing_clusters,
        "emerging_clusters": emerging_clusters,
        "discovered_clusters": discovered_clusters_summary,
        "plot_files": plot_files
    }
