# tests/test_backend_stages.py
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_upload_sysml_missing_body():
    # Should fail if no file is sent
    response = client.post("/upload-sysml")
    assert response.status_code in (400, 422)


def test_csv_not_found():
    response = client.get("/csv/nonexistent.csv")
    assert response.status_code == 404


def test_run_invalid_stage():
    response = client.post("/run-stage/999")
    assert response.status_code == 200
    assert "error" in response.json()
