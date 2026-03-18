"""
VideoMind AI - Load Test
Target: 50 concurrent users, <1% error rate

Usage:
  pip install locust
  locust -f locustfile.py --host https://videomind-ai.onrender.com --users 50 --spawn-rate 5 --run-time 60s --headless
"""
from locust import HttpUser, task, between


class VideoMindUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def homepage(self):
        self.client.get("/")

    @task(3)
    def health_check(self):
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") != "healthy":
                    resp.failure(f"Unexpected status: {data.get('status')}")
            else:
                resp.failure(f"Health check returned {resp.status_code}")

    @task(4)
    def directory(self):
        self.client.get("/directory")

    @task(2)
    def directory_api(self):
        self.client.get("/api/directory?limit=20&offset=0")

    @task(1)
    def checkout_page(self):
        self.client.get("/checkout")

    @task(1)
    def health_status_page(self):
        self.client.get("/health-status")
