import numpy as np
from app.ml.embeddings import serialize_vector, deserialize_vector, generate_embeddings_batch
from app.ml.similarity import compute_cosine_similarity, find_top_similar_reports
from app.ml.clustering import calculate_cluster_stats
from app.ml.labeling import generate_cluster_label
from app.ml.risk import calculate_cluster_risk_score
from app.ml.trend import aggregate_monthly_counts, classify_trend
from app.ml.forecast import generate_cluster_forecast


def test_vector_serialization():
    vec = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    s = serialize_vector(vec)
    d = deserialize_vector(s)
    np.testing.assert_almost_equal(vec, d, decimal=4)


def test_cosine_similarity():
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    sims = compute_cosine_similarity(v1, v2)
    assert round(float(sims[0]), 2) == 1.0
    assert round(float(sims[1]), 2) == 0.0


def test_cluster_labeling():
    reports = [
        {"description": "Worker fell from ladder", "extracted_info": {"hazards": ["Falls / Working at Height"], "equipment": ["ladder"]}},
        {"description": "Roof fall incident", "extracted_info": {"hazards": ["Falls / Working at Height"], "equipment": []}}
    ]
    label = generate_cluster_label(1, reports)
    assert label == "Falls / Working at Height"


def test_cluster_labeling_requires_hazard_dominance():
    reports = [
        {"description": "machine injury", "extracted_info": {"hazards": ["Equipment Isolation / LOTO"], "equipment": ["machine"]}},
        {"description": "unrelated injury", "extracted_info": {"hazards": [], "equipment": ["machine"]}},
        {"description": "another injury", "extracted_info": {"hazards": [], "equipment": ["machine"]}},
        {"description": "other injury", "extracted_info": {"hazards": [], "equipment": ["machine"]}},
    ]
    assert generate_cluster_label(1, reports) == "Machine Related Incidents"


def test_risk_score_calculation():
    reports = [
        {
            "timestamp": "2024-05-10",
            "extracted_info": {"hazards": ["Equipment Isolation / LOTO"], "unsafe_actions": ["No LOTO"]},
            "severity_info": {"fatality_or_catastrophe": "Fatality"}
        }
    ]
    risk = calculate_cluster_risk_score(reports, max_cluster_size=10, recent_trend_ratio=0.8)
    assert 0.0 <= risk["risk_score"] <= 100.0
    assert risk["risk_score"] > 0.0


def test_trend_classification_and_forecasting():
    monthly = [("2024-01", 5), ("2024-02", 7), ("2024-03", 10), ("2024-04", 15), ("2024-05", 22)]
    trend_class, trend_ratio = classify_trend(monthly)
    assert trend_class == "Increasing"

    fc = generate_cluster_forecast(monthly, forecast_horizon=3)
    assert len(fc) == 3
    assert "month" in fc[0] and "predicted_count" in fc[0]
