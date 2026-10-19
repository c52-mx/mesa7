from django.test import TestCase, override_settings


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

class CorsTests(TestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:8081"], CORS_ALLOW_ALL_ORIGINS=False)
    def test_preflight_allows_x_tenant_header(self):
        response = self.client.options(
            "/api/branches/",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type,x-tenant",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("x-tenant", response["Access-Control-Allow-Headers"])
