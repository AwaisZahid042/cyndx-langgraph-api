class TestSendMessage:
    def test_success(self, client, session_id):
        resp = client.post(f"/sessions/{session_id}/messages", json={"content": "What is the capital of France?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0

    def test_response_structure(self, client, session_id):
        data = client.post(f"/sessions/{session_id}/messages", json={"content": "Hello"}).json()
        for field in ("message_id", "session_id", "role", "content", "tool_calls", "usage", "latency_ms", "created_at"):
            assert field in data

    def test_message_id_format(self, client, session_id):
        data = client.post(f"/sessions/{session_id}/messages", json={"content": "test"}).json()
        assert data["message_id"].startswith("msg_")

    def test_usage_tracking(self, client, session_id):
        usage = client.post(f"/sessions/{session_id}/messages", json={"content": "test"}).json()["usage"]
        assert usage["llm_calls"] >= 1
        assert usage["total_tokens"] > 0

    def test_latency_tracked(self, client, session_id):
        assert client.post(f"/sessions/{session_id}/messages", json={"content": "test"}).json()["latency_ms"] > 0

    def test_session_not_found(self, client):
        resp = client.post("/sessions/sess_fake/messages", json={"content": "Hello"})
        assert resp.status_code == 404

    def test_empty_content(self, client, session_id):
        resp = client.post(f"/sessions/{session_id}/messages", json={"content": ""})
        assert resp.status_code == 422

    def test_missing_content(self, client, session_id):
        assert client.post(f"/sessions/{session_id}/messages", json={}).status_code == 422

    def test_multi_turn(self, client, session_id):
        r1 = client.post(f"/sessions/{session_id}/messages", json={"content": "My name is Muhammad"})
        r2 = client.post(f"/sessions/{session_id}/messages", json={"content": "What is my name?"})
        assert r1.json()["message_id"] != r2.json()["message_id"]

    def test_tool_calls_is_list(self, client, session_id):
        data = client.post(f"/sessions/{session_id}/messages", json={"content": "Hello"}).json()
        assert isinstance(data["tool_calls"], list)


class TestToolUsage:
    def test_tool_calls_populated(self, client, mock_graph_with_tools, session_id):
        from unittest.mock import patch
        sm = client.app.state.session_manager
        with patch.object(sm, "_get_or_build_graph", return_value=mock_graph_with_tools):
            data = client.post(f"/sessions/{session_id}/messages", json={"content": "Search fintech"}).json()
        assert len(data["tool_calls"]) > 0
        assert "tool_name" in data["tool_calls"][0]


class TestErrorFormat:
    def test_404_format(self, client):
        error = client.get("/sessions/sess_fake/history").json()["error"]
        assert all(k in error for k in ("code", "message", "details", "request_id"))

    def test_422_format(self, client, session_id):
        error = client.post(f"/sessions/{session_id}/messages", json={"content": ""}).json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert len(error["details"]) > 0

    def test_request_id_in_error(self, client):
        resp = client.get("/sessions/sess_fake/history")
        assert resp.json()["error"]["request_id"] == resp.headers["X-Request-ID"]
