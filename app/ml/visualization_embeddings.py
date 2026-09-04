"""PCA embedding-space diagnostic scatter plot using matplotlib.pyplot."""

import json
import random
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

from app.ml.visualization_common import database_session, ensure_output_dir
from app.models import Cluster, Report


def plot_embedding_clusters_pca(db_session=None, max_points: int = 5000) -> Optional[str]:
    """Project a reproducible sample of valid 384D embeddings onto two PCA axes."""
    with database_session(db_session) as db:
        cluster_names = dict(db.query(Cluster.id, Cluster.label).all())
        rows = db.query(Report.embedding, Report.cluster_id).filter(Report.embedding.isnot(None)).yield_per(1000)
        vectors, cluster_ids = _reservoir_sample(rows, max_points)
    if len(vectors) < 2:
        return None
    matrix = np.vstack(vectors)
    projected = PCA(n_components=2, random_state=42).fit_transform(matrix)
    unique_ids = sorted(set(cluster_ids), key=lambda value: value is not None)
    colors = plt.cm.tab20(np.linspace(0, 1, len(unique_ids)))
    fig, ax = plt.subplots(figsize=(12, 8))
    for cluster_id, color in zip(unique_ids, colors):
        mask = np.asarray([value == cluster_id for value in cluster_ids])
        label = "Noise / Outliers" if cluster_id is None else f"{cluster_names[cluster_id]} (Cluster {cluster_id})"
        ax.scatter(projected[mask, 0], projected[mask, 1], s=12, alpha=0.6, color=color, label=label)
    ax.set_xlabel("PCA Component 1")
    ax.set_ylabel("PCA Component 2")
    ax.set_title("Embedding Space by HDBSCAN Cluster")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.25)
    path = ensure_output_dir() / "embedding_clusters.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def _reservoir_sample(rows, max_points: int):
    """Keep a uniform deterministic sample without materializing all embeddings."""
    rng = random.Random(42)
    vectors, cluster_ids = [], []
    valid_count = 0
    for embedding_json, cluster_id in rows:
        try:
            vector = np.asarray(json.loads(embedding_json), dtype=np.float32)
            if vector.shape != (384,) or not np.isfinite(vector).all():
                continue
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        valid_count += 1
        if len(vectors) < max_points:
            vectors.append(vector)
            cluster_ids.append(cluster_id)
        else:
            replacement = rng.randrange(valid_count)
            if replacement < max_points:
                vectors[replacement] = vector
                cluster_ids[replacement] = cluster_id
    return vectors, cluster_ids
