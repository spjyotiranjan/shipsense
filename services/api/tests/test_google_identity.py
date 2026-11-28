import unittest

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from shipsense_api.google_identity import verify_google_id_token
from shipsense_domain.account_matching import ProviderSubject
from shipsense_domain.provider_mailbox import ProviderMailbox

NOW = 1_800_000_000
CLIENT = "ship-test.apps.googleusercontent.com"
NONCE = "server-owned-exchange-nonce"


class GoogleIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.trusted_keys = {"current-google-key": cls.key.public_key()}

    def signed(self, *, claims=None, headers=None, key=None):
        return jwt.encode(
            {
                "iss": "https://accounts.google.com",
                "sub": "stable-google-subject",
                "aud": CLIENT,
                "nonce": NONCE,
                "iat": NOW - 10,
                "exp": NOW + 120,
                "email": "ship-test@gmail.com",
                "email_verified": True,
            }
            | (claims or {}),
            key or self.key,
            algorithm="RS256",
            headers={"kid": "current-google-key"} | (headers or {}),
        )

    def verify(self, token):
        return verify_google_id_token(
            token, client_id=CLIENT, expected_nonce=NONCE, trusted_keys=self.trusted_keys, now=NOW
        )

    def test_verified_token_returns_stable_subject_and_mailbox(self):
        self.assertEqual(
            self.verify(self.signed()),
            ProviderMailbox(
                ProviderSubject("google", "stable-google-subject"), "ship-test@gmail.com"
            ),
        )

    def test_rejects_wrong_signature_key_and_token_selected_key_source(self):
        for token in (
            self.signed(key=self.other_key),
            self.signed(headers={"kid": "unknown"}),
            self.signed(headers={"jku": "https://example.invalid/keys"}),
        ):
            self.assertIsNone(self.verify(token))

    def test_rejects_wrong_issuer_audience_party_nonce_and_time(self):
        for claims in (
            {"iss": "https://example.invalid"},
            {"aud": CLIENT + "-other"},
            {"aud": [CLIENT]},
            {"azp": CLIENT + "-other"},
            {"nonce": "another-exchange"},
            {"iat": NOW + 31},
            {"nbf": NOW + 31},
            {"exp": NOW - 30, "iat": NOW - 100},
            {"iat": True},
            {"email_verified": "true"},
            {"email": "ship-test@unhosted.example"},
        ):
            with self.subTest(claims=claims):
                self.assertIsNone(self.verify(self.signed(claims=claims)))
