"""Public schema publication must not create domain access."""

import unittest

from fastapi.testclient import TestClient
from shipsense_api.main import create_app


class IdentityContractTests(unittest.TestCase):
    def test_schema_only_and_complete_public_route_inventory(self):
        app = create_app()
        schema = app.openapi()
        self.assertEqual(
            set(schema["paths"]),
            {
                "/health/live",
                "/health/ready",
                "/api/v1/version",
                "/foundation",
            },
        )
        definitions = schema["components"]["schemas"]
        for name in (
            "IdentityContract",
            "Organization",
            "Project",
            "Team",
            "Service",
            "Environment",
            "HumanPrincipal",
            "ServiceAccount",
            "RoleGrant",
        ):
            self.assertIn(name, definitions)
            self.assertFalse(definitions[name]["additionalProperties"])
        self.assertNotIn("PrincipalContext", definitions)
        with TestClient(app) as client:
            for path in (
                "/api/v1/me",
                "/api/v1/tenants/example/projects",
                "/internal/v1/auth/provider-exchanges",
            ):
                for method in (client.get, client.post):
                    response = method(path)
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(client.get("/openapi.json").status_code, 200)
