from fastapi.testclient import TestClient

from app.main import app


def test_live_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Prototipo BI asistido por IA",
        "version": "0.1.0",
        "postgres": "not_checked",
    }


def test_root_describes_service() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
