"""Diagnostic PNG visualization generation for category drill-down analysis."""

import random
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA


def plot_subcategory_risk(
    category_name: str,
    subcategories: List[Dict[str, Any]],
    noise_count: int,
    output_dir: Path
) -> Optional[Path]:
    """Plot subcategory risk scores as a clean single horizontal bar chart."""
    if not subcategories:
        return None

    # Sort subcategories by risk score descending so highest risk is at top
    sorted_subs = sorted(subcategories, key=lambda s: s["risk_score"], reverse=True)

    labels = [sub["label"] for sub in sorted_subs]
    scores = [sub["risk_score"] for sub in sorted_subs]

    fig, ax = plt.subplots(figsize=(10, max(4, 0.5 * len(labels))))
    positions = list(range(len(labels)))

    bars = ax.barh(positions, scores, color="coral", edgecolor="darkred", height=0.6)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Risk Score (0–100)", fontsize=11)
    ax.set_title(f"Subcategory Risk Scores: {category_name}", fontsize=12, fontweight="bold")
    ax.invert_yaxis()  # Highest risk at the top
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{score:.1f}", va="center", fontsize=9.5, fontweight="bold")

    cat_slug = re.sub(r'[^a-z0-9]+', '_', category_name.lower()).strip('_')
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{cat_slug}_subcategory_risk.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_subcategory_embeddings_pca(
    category_name: str,
    subcategories: List[Dict[str, Any]],
    vectors: np.ndarray,
    labels: np.ndarray,
    output_dir: Path,
    max_points: int = 5000
) -> Optional[Path]:
    """Plot 2D PCA projection of category embeddings colored by subcategory cluster."""
    n_samples = vectors.shape[0]
    if n_samples < 2:
        return None

    # Deterministic sampling ceiling for fast, reproducible plotting
    if n_samples > max_points:
        rng = random.Random(42)
        sample_indices = sorted(rng.sample(range(n_samples), max_points))
        sample_vectors = vectors[sample_indices]
        sample_labels = labels[sample_indices]
    else:
        sample_vectors = vectors
        sample_labels = labels

    pca = PCA(n_components=2, random_state=42)
    projected = pca.fit_transform(sample_vectors)

    # Subcategory mapping for legend
    sub_label_map = {sub["subcluster_num"] - 1: sub["label"] for sub in subcategories}

    unique_labels = sorted(set(sample_labels))
    colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(unique_labels))))

    fig, ax = plt.subplots(figsize=(10, 7))
    for i, cluster_lbl in enumerate(unique_labels):
        mask = (sample_labels == cluster_lbl)
        if cluster_lbl == -1:
            name = "Unclassified / Noise"
            color = "gray"
            alpha = 0.3
        else:
            name = sub_label_map.get(cluster_lbl, f"Subcategory {cluster_lbl+1}")
            color = colors[i]
            alpha = 0.7

        ax.scatter(projected[mask, 0], projected[mask, 1], label=name, color=color, alpha=alpha, s=15)

    ax.set_xlabel("PCA Component 1")
    ax.set_ylabel("PCA Component 2")
    ax.set_title(f"Subcategory Embedding Clusters ({category_name})")
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.grid(alpha=0.25)

    cat_slug = re.sub(r'[^a-z0-9]+', '_', category_name.lower()).strip('_')
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{cat_slug}_subcategory_embeddings.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path
