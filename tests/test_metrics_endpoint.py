from starlette.testclient import TestClient
from nova.api.app import app

def test_metrics_endpoint():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b'nova_governance_runs_total' in resp.content
