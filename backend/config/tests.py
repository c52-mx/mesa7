from django.test import TestCase


class HealthTests(TestCase):
    def test_health_ok(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_token_rejects_bad_credentials(self):
        response = self.client.post(
            "/api/auth/login/", {"email": "nadie@x.com", "password": "x"}
        )
        self.assertEqual(response.status_code, 401)
