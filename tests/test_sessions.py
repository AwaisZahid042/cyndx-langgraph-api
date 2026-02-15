class TestCreateSession:
    def test_default_config(self, client):
        resp = client.post("/sessions", json={})
        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"].startswith("sess_")
        assert data["status"] == "active"
        assert data["agent_config"]["model"] == "gpt-4o-mini"

    def test_custom_config(self, client):
        resp = client.post("/sessions", json={"agent_config": {"model": "claude-3-5-haiku-20241022", "temperature": 0.3}})
        assert resp.status_code == 201
        assert resp.json()["agent_config"]["model"] == "claude-3-5-haiku-20241022"

    def test_unique_ids(self, client):
        ids = {client.post("/sessions", json={}).json()["session_id"] for _ in range(5)}
        assert len(ids) == 5

    def test_no_body(self, client):
        assert client.post("/sessions").status_code == 201

    def test_invalid_temperature(self, client):
        resp = client.post("/sessions", json={"agent_config": {"temperature": 5.0}})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


class TestGetHistory:
    def test_empty_session(self, client, session_id):
        data = client.get(f"/sessions/{session_id}/history").json()
        assert data["message_count"] == 0

    def test_not_found(self, client):
        assert client.get("/sessions/sess_fake/history").status_code == 404

    def test_after_message(self, client, session_id):
        client.post(f"/sessions/{session_id}/messages", json={"content": "Hello"})
        data = client.get(f"/sessions/{session_id}/history").json()
        assert data["message_count"] == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"


class TestDeleteSession:
    def test_delete(self, client, session_id):
        resp = client.delete(f"/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "terminated"

    def test_not_found(self, client):
        assert client.delete("/sessions/sess_fake").status_code == 404

    def test_double_delete(self, client, session_id):
        client.delete(f"/sessions/{session_id}")
        resp = client.delete(f"/sessions/{session_id}")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SESSION_TERMINATED"

    def test_message_after_delete(self, client, session_id):
        client.delete(f"/sessions/{session_id}")
        resp = client.post(f"/sessions/{session_id}/messages", json={"content": "Hello"})
        assert resp.status_code == 400
