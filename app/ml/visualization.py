"""Matplotlib diagnostic plot entry points for the OSHA pipeline."""

from typing import Dict, Optional

from app.ml.visualization_charts import plot_cluster_distribution, plot_risk_scores
from app.ml.visualization_embeddings import plot_embedding_clusters_pca
from app.ml.visualization_time import plot_forecasts, plot_temporal_trends


def generate_all_diagnostics(db_session=None) -> Dict[str, Optional[str]]:
    """Generate backend diagnostics as PNG files in ``output/plots``."""
    return {
        "cluster_distribution": plot_cluster_distribution(db_session),
        "risk_scores": plot_risk_scores(db_session),
        "temporal_trends": plot_temporal_trends(db_session),
        "forecasts": plot_forecasts(db_session),
        "embedding_clusters": plot_embedding_clusters_pca(db_session),
    }
