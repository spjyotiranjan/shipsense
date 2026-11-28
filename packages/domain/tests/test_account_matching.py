import unittest
from uuid import UUID

from shipsense_domain.account_matching import (
    DirectoryAccount,
    ProviderSubject,
    VerifiedProviderIdentity,
    match_sign_in,
)


class Directory:
    def __init__(self):
        self.subjects = {}
        self.emails = {}
        self.calls = []

    def by_subject(self, subject):
        self.calls.append("subject")
        return self.subjects.get(subject)

    def by_email_key(self, key):
        self.calls.append("email")
        return self.emails.get(key)


class AccountMatchingTests(unittest.TestCase):
    def setUp(self):
        self.directory = Directory()
        self.subject = ProviderSubject("google", "stable-subject")
        self.identity = VerifiedProviderIdentity(self.subject, "person@example.com")
        self.account = DirectoryAccount(UUID(int=1), "person@example.com", "active")

    def test_returning_subject_resolves_without_email_lookup(self):
        self.directory.subjects[self.subject] = self.account
        result = match_sign_in(self.identity, self.directory)
        self.assertEqual(result.outcome, "returning")
        self.assertEqual(result.account_id, self.account.id)
        self.assertEqual(self.directory.calls, ["subject"])

    def test_unbound_same_email_has_no_implicit_link_or_account_id(self):
        self.directory.emails[self.account.email_key] = self.account
        result = match_sign_in(self.identity, self.directory)
        self.assertEqual(result.outcome, "unavailable")
        self.assertIsNone(result.account_id)
        self.assertEqual(self.directory.calls, ["subject", "email"])

    def test_changed_email_does_not_fall_back_or_return_binding(self):
        self.directory.subjects[self.subject] = DirectoryAccount(
            UUID(int=1), "previous@example.com", "active"
        )
        result = match_sign_in(self.identity, self.directory)
        self.assertEqual(result.outcome, "unavailable")
        self.assertIsNone(result.account_id)
        self.assertEqual(self.directory.calls, ["subject"])

    def test_suspended_binding_denied_without_email_lookup(self):
        self.directory.subjects[self.subject] = DirectoryAccount(
            self.account.id, self.account.email_key, "suspended"
        )
        self.assertEqual(match_sign_in(self.identity, self.directory).outcome, "unavailable")
        self.assertEqual(self.directory.calls, ["subject"])

    def test_unused_email_is_a_registration_candidate_not_an_account(self):
        result = match_sign_in(self.identity, self.directory)
        self.assertEqual(result.outcome, "registration_candidate")
        self.assertIsNone(result.account_id)
