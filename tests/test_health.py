from app.config import get_settings


class TestHealthCheck:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_response_structure(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "checks" in data

    def test_dependency_checks(self, client):
        checks = client.get("/health").json()["checks"]
        assert checks["llm_provider"] == "ok"
        assert checks["checkpoint_store"] == "ok"

    def test_correct_version(self, client):
        assert client.get("/health").json()["version"] == get_settings().app_version

    def test_has_request_id_header(self, client):
        resp = client.get("/health")
        assert resp.headers["X-Request-ID"].startswith("req_")
