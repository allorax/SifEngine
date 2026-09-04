"""Cluster and risk diagnostic charts using matplotlib.pyplot only."""

from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from app.ml.visualization_common import database_session, ensure_output_dir
from app.models import Cluster, Report, RiskScore


def _save(fig, filename: str) -> str:
    path = ensure_output_dir() / filename
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def plot_cluster_distribution(db_session=None) -> Optional[str]:
    """Plot discovered cluster counts and any unassigned noise reports."""
    with database_session(db_session) as db:
        clusters = db.query(Cluster).order_by(Cluster.report_count.desc()).all()
        labels = [cluster.label for cluster in clusters]
        counts = [cluster.report_count for cluster in clusters]
        noise_count = db.query(Report).filter(Report.cluster_id.is_(None)).count()
    if noise_count:
        labels.append("Noise / Outliers")
        counts.append(noise_count)
    if not counts:
        return None
    fig, ax = plt.subplots(figsize=(12, max(4, 0.5 * len(labels))))
    positions = list(range(len(labels)))
    bars = ax.barh(positions, counts, color="steelblue")
    ax.set_yticks(positions, labels)
    ax.set_xlabel("Number of Reports")
    ax.set_title("OSHA Report Distribution Across Clusters")
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f" {count}", va="center")
    return _save(fig, "cluster_distribution.png")


def plot_risk_scores(db_session=None) -> Optional[str]:
    """Plot the actual 0–100 risk score for every discovered cluster."""
    with database_session(db_session) as db:
        rows = db.query(Cluster, RiskScore).join(RiskScore).order_by(RiskScore.risk_score.desc()).all()
        labels = [cluster.label for cluster, _ in rows]
        scores = [risk.risk_score for _, risk in rows]
    if not scores:
        return None
    fig, ax = plt.subplots(figsize=(max(10, 1.2 * len(labels)), 6))
    positions = list(range(len(labels)))
    bars = ax.bar(positions, scores, color="coral", edgecolor="darkred")
    ax.set_xticks(positions, labels, rotation=35, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Risk Score (0–100)")
    ax.set_title("Cluster Risk Scores")
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, score + 1, f"{score:.1f}", ha="center")
    return _save(fig, "risk_scores.png")
