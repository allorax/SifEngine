"""Historical activity and forecast trajectory charts using matplotlib.pyplot."""

import json
import math
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from app.ml.trend import aggregate_monthly_counts
from app.ml.visualization_common import database_session, ensure_output_dir
from app.models import Cluster, Forecast, Report


def _save(fig, filename: str) -> str:
    path = ensure_output_dir() / filename
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def _cluster_months(db, cluster_id: int):
    timestamps = db.query(Report.timestamp).filter(Report.cluster_id == cluster_id).all()
    return aggregate_monthly_counts([{"timestamp": timestamp} for timestamp, in timestamps])


def _set_month_ticks(ax, labels, max_ticks: int = 12) -> None:
    """Keep long multi-year charts readable without hiding the time range."""
    step = max(1, math.ceil(len(labels) / max_ticks))
    positions = list(range(0, len(labels), step))
    if positions[-1] != len(labels) - 1:
        positions.append(len(labels) - 1)
    ax.set_xticks(positions, [labels[position] for position in positions], rotation=45, ha="right")


def plot_temporal_trends(db_session=None) -> Optional[str]:
    """Plot actual monthly report activity for discovered clusters."""
    with database_session(db_session) as db:
        series = [(f"{cluster.label} (Cluster {cluster.cluster_num})", _cluster_months(db, cluster.id))
                  for cluster in db.query(Cluster).order_by(Cluster.report_count.desc()).all()]
    series = [(label, months) for label, months in series if months]
    if not series:
        return None
    fig, axes = plt.subplots(len(series), 1, figsize=(12, max(4, 3 * len(series))), squeeze=False)
    for ax, (label, months) in zip(axes[:, 0], series):
        labels, counts = zip(*months)
        positions = list(range(len(labels)))
        ax.bar(positions, counts, color="mediumseagreen", alpha=0.8)
        ax.set_title(f"Historical Activity: {label}")
        ax.set_ylabel("Reports")
        _set_month_ticks(ax, labels)
        ax.grid(axis="y", alpha=0.25)
    axes[-1, 0].set_xlabel("Month")
    return _save(fig, "temporal_trends.png")


def plot_forecasts(db_session=None) -> Optional[str]:
    """Plot historical activity and model forecast trajectories, not predictions."""
    with database_session(db_session) as db:
        rows = db.query(Cluster, Forecast).join(Forecast).order_by(Cluster.report_count.desc()).all()
        series = [(f"{cluster.label} (Cluster {cluster.cluster_num})", _cluster_months(db, cluster.id), json.loads(forecast.forecast_json))
                  for cluster, forecast in rows]
    series = [(label, history, future) for label, history, future in series
              if len(history) >= 6 and future]
    if not series:
        return None
    fig, axes = plt.subplots(len(series), 1, figsize=(12, max(4, 3 * len(series))), squeeze=False)
    for ax, (label, history, future) in zip(axes[:, 0], series):
        historical_months, historical_counts = zip(*history)
        future_months = [point["month"] for point in future]
        future_counts = [point["predicted_count"] for point in future]
        labels = list(historical_months) + future_months
        positions = list(range(len(labels)))
        ax.plot(positions[:len(history)], historical_counts, marker="o", label="Historical activity")
        ax.plot(positions[len(history) - 1:], [historical_counts[-1], *future_counts], "--o",
                label="Forecast trajectory")
        ax.axvline(len(history) - 0.5, color="gray", linestyle=":")
        ax.set_title(f"Precursor Activity Trajectory: {label}")
        ax.set_ylabel("Reports")
        _set_month_ticks(ax, labels)
        ax.legend()
        ax.grid(alpha=0.25)
    axes[-1, 0].set_xlabel("Month — trajectory only; not an accident prediction")
    return _save(fig, "forecasts.png")
