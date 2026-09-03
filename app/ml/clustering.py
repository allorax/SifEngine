from collections import Counter
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.preprocessing import normalize
from app.config import HDBSCAN_MIN_CLUSTER_SIZE, HDBSCAN_MIN_SAMPLES


def run_hdbscan_clustering(matrix: np.ndarray, min_cluster_size: int = HDBSCAN_MIN_CLUSTER_SIZE, min_samples: int = HDBSCAN_MIN_SAMPLES) -> np.ndarray:
    """Run HDBSCAN on vector matrix and return cluster labels array.

    For semantic embeddings (high-dimensional), we normalize vectors to unit length
    and use euclidean distance, which approximates cosine similarity.
    """
    if matrix.shape[0] < min_cluster_size:
        # Adjust min_cluster_size if dataset is smaller
        adjusted_min_size = max(3, min(min_cluster_size, matrix.shape[0] // 2))
        print(f"[DEBUG] Dataset size ({matrix.shape[0]}) < min_cluster_size ({min_cluster_size}). Adjusting to {adjusted_min_size}")
        min_cluster_size = adjusted_min_size

    try:
        import hdbscan

        # Normalize vectors to unit length for semantic embeddings
        # This converts euclidean distance to cosine similarity
        normalized_matrix = normalize(matrix, norm='l2')

        print(f"[DEBUG] Running HDBSCAN: samples={matrix.shape[0]}, dims={matrix.shape[1]}, min_cluster_size={min_cluster_size}, min_samples={min_samples}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean'
        )
        labels = clusterer.fit_predict(normalized_matrix)

        unique_labels = np.unique(labels)
        n_clusters = len([l for l in unique_labels if l != -1])
        n_noise = (labels == -1).sum()
        print(f"[DEBUG] HDBSCAN result: {n_clusters} clusters, {n_noise} noise points")

        return labels
    except Exception as e:
        print(f"Warning: HDBSCAN error ({e}). Fallback to K-Means.")
        try:
            from sklearn.cluster import KMeans
            n_clusters = max(2, min(8, matrix.shape[0] // min_cluster_size))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            return kmeans.fit_predict(matrix)
        except Exception:
            return np.zeros(matrix.shape[0], dtype=int)


def calculate_cluster_stats(cluster_num: int, reports: List[Dict[str, Any]], total_dataset_size: int) -> Dict[str, Any]:
    """Calculate summary statistics for a cluster of reports."""
    count = len(reports)
    percentage = round((count / total_dataset_size) * 100.0, 2) if total_dataset_size > 0 else 0.0

    events = [r.get("event") for r in reports if r.get("event")]
    industries = [r.get("industry") for r in reports if r.get("industry")]
    states = [r.get("state") for r in reports if r.get("state")]
    
    hazards = []
    for r in reports:
        ext = r.get("extracted_info") or {}
        if isinstance(ext, dict) and "hazards" in ext:
            hazards.extend(ext["hazards"])

    dates = [r.get("timestamp") for r in reports if r.get("timestamp")]

    dominant_event = Counter(events).most_common(1)[0][0] if events else "General Safety Incident"
    dominant_hazard = Counter(hazards).most_common(1)[0][0] if hazards else "General Hazard Pattern"
    dominant_industry = Counter(industries).most_common(1)[0][0] if industries else "Various Industries"
    dominant_state = Counter(states).most_common(1)[0][0] if states else "Various States"

    min_date = min(dates) if dates else None
    max_date = max(dates) if dates else None

    return {
        "cluster_num": cluster_num,
        "report_count": count,
        "percentage": percentage,
        "dominant_event": dominant_event,
        "dominant_hazard": dominant_hazard,
        "dominant_industry": dominant_industry,
        "dominant_state": dominant_state,
        "min_date": min_date,
        "max_date": max_date
    }
