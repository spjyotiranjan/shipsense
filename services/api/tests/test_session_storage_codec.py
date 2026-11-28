import unittest
from uuid import UUID

from bson import BSON, Int64
from shipsense_api.session_storage_codec import (
    InvalidStorageRecord,
    decode_account,
    decode_session,
    encode_audit,
)
from shipsense_domain.sessions import SessionAudit

ACCOUNT = UUID("00000000-0000-0000-0000-00000000000a")
DIGEST = "a" * 64


class SessionStorageCodecTests(unittest.TestCase):
    def setUp(self):
        self.session = dict(
            _id=DIGEST,
            schema_version=1,
            fence=Int64(1),
            account_id=str(ACCOUNT),
            authentication_epoch=Int64(2),
            created_at=Int64(1000),
            last_activity_at=Int64(1100),
            absolute_expires_at=Int64(1900),
            idle_expires_at=Int64(1700),
            revoked_at=None,
            revision=Int64(3),
        )
        self.account = dict(
            _id=str(ACCOUNT),
            schema_version=1,
            fence=Int64(4),
            authentication_epoch=Int64(2),
            status="active",
            revision=Int64(1),
        )

    def test_session_and_account_decode_bson_int64_and_exact_lookup_keys(self):
        record = decode_session(BSON.encode(self.session).decode(), DIGEST)
        account = decode_account(BSON.encode(self.account).decode(), ACCOUNT)
        self.assertEqual(record.account_id, account.account_id)
        self.assertEqual(record.authentication_epoch, account.authentication_epoch)
        self.assertEqual(record.revision, 3)
        with self.assertRaises(InvalidStorageRecord):
            decode_session(self.session, "b" * 64)
        with self.assertRaises(InvalidStorageRecord):
            decode_account(self.account, UUID(int=90))

    def test_malformed_shape_version_and_narrow_bson_types_are_rejected(self):
        for overrides in (
            {"schema_version": True},
            {"schema_version": 2},
            {"fence": 1},
            {"fence": Int64(-1)},
            {"account_id": str(ACCOUNT).upper()},
            {"idle_expires_at": Int64(1701)},
            {"revoked_at": "1000"},
            {"extra": "private"},
            {"revision": 3},
            {"revision": Int64(2**63)},
        ):
            with (
                self.subTest(overrides=overrides),
                self.assertRaisesRegex(InvalidStorageRecord, "^Invalid session storage record[.]$"),
            ):
                decode_session(self.session | overrides, DIGEST)
        session = self.session.copy()
        del session["revoked_at"]
        with self.assertRaises(InvalidStorageRecord):
            decode_session(session, DIGEST)
        with self.assertRaises(InvalidStorageRecord):
            decode_account(self.account | {"status": "invalid"}, ACCOUNT)

    def test_audit_document_contains_only_redacted_receipt_fields(self):
        event_id = UUID(int=50)
        event = SessionAudit(
            event_id=event_id,
            action="session.resolve",
            outcome="denied",
            recorded_at=1200,
            correlation_id="00000000-0000-4000-8000-000000000003",
        )
        document = BSON.encode(encode_audit(event)).decode()
        self.assertEqual(
            document,
            dict(
                _id=str(event_id),
                schema_version=1,
                partition="authentication",
                actor="shipsense-bff",
                action="session.resolve",
                outcome="denied",
                recorded_at=Int64(1200),
                correlation_id="00000000-0000-4000-8000-000000000003",
            ),
        )
        self.assertIs(type(document["recorded_at"]), Int64)
        with self.assertRaises(InvalidStorageRecord):
            encode_audit(event.model_copy(update={"recorded_at": 2**63}))
