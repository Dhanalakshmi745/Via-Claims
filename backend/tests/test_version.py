from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_version():
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0"}