from locust import HttpUser, between, task


class ConversationUser(HttpUser):
    wait_time = between(1, 3)
    session_id = None

    def on_start(self):
        resp = self.client.post("/sessions", json={"agent_config": {"model": "gpt-4o-mini"}})
        if resp.status_code == 201:
            self.session_id = resp.json()["session_id"]

    def on_stop(self):
        if self.session_id:
            self.client.delete(f"/sessions/{self.session_id}")

    @task(5)
    def send_message(self):
        if self.session_id:
            self.client.post(f"/sessions/{self.session_id}/messages", json={"content": "What are the latest trends in fintech?"})

    @task(2)
    def get_history(self):
        if self.session_id:
            self.client.get(f"/sessions/{self.session_id}/history")

    @task(1)
    def health_check(self):
        self.client.get("/health")
