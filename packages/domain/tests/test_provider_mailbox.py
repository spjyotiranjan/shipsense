import unittest

from shipsense_domain.account_matching import ProviderSubject
from shipsense_domain.provider_mailbox import ProviderMailbox, github_mailbox, google_mailbox


class ProviderMailboxTests(unittest.TestCase):
    def test_google_accepts_verified_gmail_and_hosted_mail_without_rewriting(self):
        for fields in (
            {"email": "Account+Tag@GMAIL.COM"},
            {"email": "Account@workspace.example", "hd": "workspace.example"},
        ):
            with self.subTest(fields=fields):
                self.assertEqual(
                    google_mailbox({"sub": "123456", "email_verified": True, **fields}),
                    ProviderMailbox(ProviderSubject("google", "123456"), fields["email"]),
                )

    def test_google_rejects_verified_third_party_mail_and_unverified_hosted_mail(self):
        self.assertIsNone(
            google_mailbox({"sub": "123456", "email_verified": True, "email": "a@other.example"})
        )
        self.assertIsNone(
            google_mailbox({"sub": "123456", "email_verified": False, "email": "a@gmail.com"})
        )
        self.assertIsNone(
            google_mailbox({"sub": "123456", "email_verified": "true", "email": "a@gmail.com"})
        )

    def test_github_uses_numeric_id_and_authenticated_private_primary(self):
        self.assertEqual(
            github_mailbox(
                {"id": 123, "login": "renamable", "email": "profile@example.invalid"},
                [
                    {"email": "alternate@example.invalid", "primary": False, "verified": True},
                    {"email": "Private@example.invalid", "primary": True, "verified": True},
                ],
            ),
            ProviderMailbox(ProviderSubject("github", "123"), "Private@example.invalid"),
        )

    def test_github_refuses_public_profile_as_proof_and_ambiguous_primary(self):
        profile = {"id": 123, "email": "profile@example.invalid"}
        primary = {"email": "primary@example.invalid", "primary": True, "verified": True}
        for emails in (
            [],
            [None],
            {"emails": [primary]},
            [dict(primary, verified=False)],
            [dict(primary, email="123+account@users.noreply.github.com")],
            [primary, primary],
        ):
            with self.subTest(emails=emails):
                self.assertIsNone(github_mailbox(profile, emails))
        self.assertIsNone(github_mailbox({"id": True}, [primary]))
