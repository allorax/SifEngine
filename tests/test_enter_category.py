"""Test suite for enter_category CLI and drill-down service."""

import pytest
import json
import numpy as np
from app.services.category_drilldown import execute_category_drilldown
from app.models import Report, Cluster, RiskScore


@pytest.fixture
def populated_db(db_session):
    """Fixture providing a populated test DB with clusters, reports, and embeddings."""
    # Check if cluster exists
    cluster = db_session.query(Cluster).filter(Cluster.label == "Falls / Working at Height").first()
    if not cluster:
        cluster = Cluster(
            cluster_num=1,
            label="Falls / Working at Height",
            report_count=3,
            percentage=100.0,
            dominant_event="Fall to lower level",
            dominant_hazard="Falls / Working at Height"
        )
        db_session.add(cluster)
        db_session.flush()

        dummy_vec = list(np.random.randn(384).astype(float))
        reports = [
            Report(
                description="Worker fell 10ft from a ladder while painting",
                event="Fall to lower level",
                extracted_info=json.dumps({"hazards": ["Falls / Working at Height"], "equipment": ["ladder"]}),
                embedding=json.dumps(dummy_vec),
                cluster_id=cluster.id
            ),
            Report(
                description="Employee fell off roof edge during roofing work",
                event="Fall to lower level",
                extracted_info=json.dumps({"hazards": ["Falls / Working at Height"], "equipment": []}),
                embedding=json.dumps(dummy_vec),
                cluster_id=cluster.id
            ),
            Report(
                description="Scaffold collapse caused worker to fall 15 feet",
                event="Fall from scaffold",
                extracted_info=json.dumps({"hazards": ["Falls / Working at Height"], "equipment": ["scaffold"]}),
                embedding=json.dumps(dummy_vec),
                cluster_id=cluster.id
            ),
        ]
        db_session.add_all(reports)
        db_session.commit()

    return db_session


def test_enter_category_valid(populated_db):
    result = execute_category_drilldown(populated_db, category_input="Falls / Working at Height", generate_plots=False)
    assert result["status"] == "success"
    assert "subcategories" in result
    assert result["category_records"] == 3
    assert result["total_dataset_records"] >= 3


def test_enter_category_invalid(populated_db):
    result = execute_category_drilldown(populated_db, category_input="non-existent-category-12345", generate_plots=False)
    assert result["status"] == "category_not_found"
    assert "available" in result
    assert len(result["available"]) > 0


def test_category_resolution_case_insensitive(populated_db):
    result_lower = execute_category_drilldown(populated_db, category_input="falls", generate_plots=False)
    result_upper = execute_category_drilldown(populated_db, category_input="FALLS", generate_plots=False)
    assert result_lower["status"] == "success"
    assert result_upper["status"] == "success"
    assert result_lower["category"] == result_upper["category"]


def test_show_categories_db(populated_db):
    clusters = populated_db.query(Cluster).filter(Cluster.cluster_num != -1).all()
    assert len(clusters) >= 1
    assert clusters[0].label == "Falls / Working at Height"
