import pytest
from fastapi.testclient import TestClient
from comedy_duo.control_panel import create_app
from comedy_duo.models import Settings


@pytest.fixture
def app():
    settings = Settings()
    return create_app(settings, event_callback=lambda e: None)


@pytest.fixture
def client(app):
    return TestClient(app)


class TestControlPanel:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_inject_event(self, client):
        response = client.post("/event", json={"text": "she dropped the database"})
        assert response.status_code == 200
        assert response.json()["status"] == "injected"

    def test_get_settings(self, client):
        response = client.get("/settings")
        assert response.status_code == 200
        assert "cooldown_seconds" in response.json()

    def test_update_settings(self, client):
        response = client.patch("/settings", json={"cooldown_seconds": 60})
        assert response.status_code == 200
        assert response.json()["cooldown_seconds"] == 60

    def test_kill_switch(self, client):
        response = client.post("/kill")
        assert response.status_code == 200

    def test_control_page_renders(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
