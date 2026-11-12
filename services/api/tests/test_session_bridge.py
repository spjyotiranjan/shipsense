"""Actual signatures, Node interoperability and canonical authority failure boundaries."""

import base64
import json
import subprocess
import time
import unittest
from dataclasses import replace
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi.testclient import TestClient
from shipsense_api.main import create_app
from shipsense_api.service_credentials import (
    InvalidServiceCredential,
    ServiceKey,
    verify_service_credential,
)
from shipsense_api.session_bridge import SessionDenied, SessionSnapshot

ROOT = Path(__file__).resolve().parents[3]
HANDLE = "s" * 43


class FixtureAuthority:
    """Test fixture only; never composed in the product runtime."""

    def __init__(self, now):
        self.now = now
        self.revoked = False
        self.outage = False
        self.correlations = []

    async def resolve(self, handle, correlation_id):
        self.correlations.append(correlation_id)
        if self.outage:
            raise RuntimeError("secret provider details")
        if self.revoked or handle != HANDLE:
            raise SessionDenied()
        return SessionSnapshot(
            createdAt=self.now - 400,
            lastActivityAt=self.now - 100,
            absoluteExpiresAt=self.now + 500,
            idleExpiresAt=self.now + 500,
        )

    async def revoke(self, handle, correlation_id):
        self.correlations.append(correlation_id)
        if self.outage:
            raise RuntimeError("secret provider details")
        self.revoked = True


class SessionBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.pem = cls.private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def setUp(self):
        self.now = int(time.time())
        self.key = ServiceKey(self.pem, "active", self.now - 1000, self.now + 1000)
        self.keys = {"current": self.key}
        self.claims = dict(
            iss="shipsense-web",
            aud="shipsense-auth",
            sub="shipsense-bff",
            scope="session:resolve",
            iat=self.now,
            nbf=self.now,
            exp=self.now + 60,
            jti="correlation-credential-001",
        )

    def token(self, claims=None, headers=None):
        return jwt.encode(
            self.claims if claims is None else claims,
            self.private,
            algorithm="RS256",
            headers=headers or {"kid": "current"},
        )

    def verify(self, token, keys=None, now=None, skew=30):
        verify_service_credential(
            token,
            "session:resolve",
            self.keys if keys is None else keys,
            self.now if now is None else now,
            skew,
        )

    def raw_token(self, header, body):
        def segment(value):
            return base64.urlsafe_b64encode(value.encode()).rstrip(b"=")

        data = segment(header) + b"." + segment(body)
        signature = self.private.sign(data, padding.PKCS1v15(), hashes.SHA256())
        return (data + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()

    def test_valid_rotation_overlap_and_retirement(self):
        self.verify(self.token())
        second = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = second.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        registry = {**self.keys, "next": replace(self.key, public_pem=pem)}
        following = jwt.encode(self.claims, second, algorithm="RS256", headers={"kid": "next"})
        self.verify(following, keys=registry)
        self.verify(self.token(), keys=registry)
        with self.assertRaises(InvalidServiceCredential):
            self.verify(
                self.token(), keys={**registry, "current": replace(self.key, status="retired")}
            )
        with self.assertRaises(InvalidServiceCredential):
            self.verify(following)

    def test_claim_types_scope_audience_lifetime_and_boundaries(self):
        mutations = [
            {"iss": "attacker"},
            {"aud": ["shipsense-auth"]},
            {"sub": "worker"},
            {"scope": "session:revoke"},
            {"scope": ["session:resolve"]},
            {"iat": True},
            {"exp": str(self.now + 60)},
            {"iat": 1.5},
            {"nbf": self.now + 1},
            {"exp": self.now + 61},
            {"exp": self.now},
            {"iat": self.now + 31, "nbf": self.now + 31, "exp": self.now + 60},
            {"jti": "short"},
            {"extra": "not allowed"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(InvalidServiceCredential):
                self.verify(self.token({**self.claims, **mutation}))
        for field in self.claims:
            with self.subTest(missing=field), self.assertRaises(InvalidServiceCredential):
                self.verify(self.token({k: v for k, v in self.claims.items() if k != field}))
        token = self.token()
        self.verify(token, now=self.now + 89)
        with self.assertRaises(InvalidServiceCredential):
            self.verify(token, now=self.now + 90)
        with self.assertRaises(InvalidServiceCredential):
            self.verify(token, skew=31)

    def test_duplicate_claim_header_algorithm_key_and_size_rejections(self):
        header = '{"alg":"RS256","typ":"JWT","kid":"current"}'
        claims = json.dumps(self.claims)
        cases = [
            self.raw_token(header, claims[:-1] + ',"aud":"shipsense-auth"}'),
            self.raw_token(header[:-1] + ',"kid":"current"}', claims),
            self.raw_token(header[:-1] + ',"jku":"https://attacker.invalid"}', claims),
            self.raw_token(header.replace("RS256", "HS256"), claims),
            self.raw_token(header.replace("RS256", "none"), claims),
            self.token(headers={"kid": "unknown"}),
            self.token()[:-10] + "tampered",
            "x" * 4097,
            "..",
            "bad",
        ]
        for token in cases:
            with self.subTest(case=cases.index(token)), self.assertRaises(InvalidServiceCredential):
                self.verify(token)
        for key in [
            replace(self.key, not_before=self.now + 1),
            replace(self.key, not_after=self.now),
            replace(self.key, public_pem=b"invalid"),
        ]:
            with self.assertRaises(InvalidServiceCredential):
                self.verify(self.token(), keys={"current": key})

    def test_node_signer_python_verifier_interoperability(self):
        private_pem = self.private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        # Ephemeral private key passes through stdin only, never args/files/logs.
        script = """
import { serviceCredential } from './apps/web/src/lib/server/service-credential.ts';
let input = ''; for await (const chunk of process.stdin) input += chunk;
const data = JSON.parse(input);
process.stdout.write(serviceCredential(data.key, 'session:resolve', data.now));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT,
            input=json.dumps(
                {
                    "key": {
                        "kid": "current",
                        "privatePem": private_pem,
                        "status": "active",
                        "notBefore": self.key.not_before,
                        "notAfter": self.key.not_after,
                    },
                    "now": self.now,
                }
            ),
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        self.verify(result.stdout)

    def test_api_independent_authority_revocation_audit_and_outage(self):
        authority = FixtureAuthority(self.now)
        with TestClient(create_app(session_authority=authority, service_keys=self.keys)) as client:
            path = "/internal/v1/auth/session/"
            headers = {"Authorization": "Bearer " + self.token(), "X-Request-ID": "bridge-test"}
            response = client.post(path + "resolve", json={"handle": HANDLE}, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                set(response.json()),
                {"createdAt", "lastActivityAt", "absoluteExpiresAt", "idleExpiresAt"},
            )
            self.assertEqual(authority.correlations, ["bridge-test"])
            authority.outage = True
            with self.assertLogs("shipsense.diagnostics", level="INFO") as logs:
                response = client.post(path + "resolve", json={"handle": HANDLE}, headers=headers)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("secret", response.text + str(logs.output))
            self.assertNotIn(HANDLE, response.text + str(logs.output))
            authority.outage = False
            revoke_headers = {
                **headers,
                "Authorization": "Bearer " + self.token({**self.claims, "scope": "session:revoke"}),
            }
            for _ in range(2):
                self.assertEqual(
                    client.post(
                        path + "revoke", json={"handle": HANDLE}, headers=revoke_headers
                    ).json(),
                    {"state": "revoked"},
                )
            response = client.post(path + "resolve", json={"handle": HANDLE}, headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_default_and_browser_credentials_have_no_api_authority(self):
        with TestClient(create_app()) as client:
            for headers in [
                {},
                {"Authorization": "Bearer " + self.token()},
                {"Cookie": "next-auth.session-token=encrypted"},
            ]:
                response = client.post(
                    "/internal/v1/auth/session/resolve", json={"handle": HANDLE}, headers=headers
                )
                self.assertEqual(response.status_code, 401)
        with TestClient(create_app(service_keys=self.keys)) as client:
            response = client.post(
                "/internal/v1/auth/session/resolve",
                json={"handle": HANDLE},
                headers={"Authorization": "Bearer " + self.token()},
            )
            self.assertEqual(response.status_code, 503)

    def test_snapshot_expiry_bounds_and_malformed_payload(self):
        valid = dict(
            createdAt=self.now - 500,
            lastActivityAt=self.now - 100,
            absoluteExpiresAt=self.now + 400,
            idleExpiresAt=self.now + 500,
        )
        SessionSnapshot(**valid).check(self.now)
        for change in [
            {"absoluteExpiresAt": self.now + 401},
            {"idleExpiresAt": self.now + 501},
            {"idleExpiresAt": self.now},
            {"lastActivityAt": self.now + 1},
        ]:
            with self.assertRaises(SessionDenied):
                SessionSnapshot(**{**valid, **change}).check(self.now)
        with TestClient(create_app(service_keys=self.keys)) as client:
            for body in [{"handle": "bad"}, {"handle": HANDLE, "role": "admin"}, {"handle": 123}]:
                self.assertEqual(
                    client.post("/internal/v1/auth/session/resolve", json=body).status_code, 422
                )
