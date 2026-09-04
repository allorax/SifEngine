import matplotlib
matplotlib.use('Agg')
import json

import numpy as np

from app.ml.visualization import generate_all_diagnostics
from app.models import Cluster, Forecast, Report, RiskScore


def test_diagnostics_generate_png_files(db_session, monkeypatch, tmp_path):
    """Diagnostics use actual SQLite data and save every graph as a PNG."""
    monkeypatch.setattr("app.ml.visualization_common.OUTPUT_DIR", tmp_path / "plots")
    cluster = Cluster(cluster_num=0, label="Falls", report_count=6, percentage=100.0)
    db_session.add(cluster)
    db_session.flush()
    for index, timestamp in enumerate((
        "2024-01-10", "2024-02-10", "2024-03-10", "2024-04-10", "2024-05-10", "2024-06-10"
    )):
        vector = np.zeros(384, dtype=np.float32)
        vector[index] = 1.0
        db_session.add(Report(source_dataset="test", description="fall incident", timestamp=timestamp,
                              embedding=json.dumps(vector.tolist()), cluster_id=cluster.id))
    db_session.add(RiskScore(cluster_id=cluster.id, risk_score=75, frequency=50,
                             near_miss_intensity=50, severity=50, trend=50, recency=50))
    db_session.add(Forecast(cluster_id=cluster.id, trend_classification="Increasing",
                            forecast_json=json.dumps([{"month": "2024-07", "predicted_count": 3.0}])))
    db_session.commit()

    plots = generate_all_diagnostics(db_session)

    assert set(plots) == {"cluster_distribution", "risk_scores", "temporal_trends", "forecasts", "embedding_clusters"}
    assert all(path and path.endswith(".png") for path in plots.values())
    assert all((tmp_path / "plots" / f"{name}.png").is_file() for name in (
        "cluster_distribution", "risk_scores", "temporal_trends", "forecasts", "embedding_clusters"
    ))
