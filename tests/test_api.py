def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_reports_endpoint_empty(client):
    response = client.get("/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_clusters_endpoint_empty(client):
    response = client.get("/clusters")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_summary_empty(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "total_clusters" in data
    assert "top_risk_clusters" in data
