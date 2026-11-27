import unittest
from datetime import timedelta
from uuid import uuid4

from shipsense_domain.audit_timeline import AuditRecord, InvalidTimeline, TimelineReader
from shipsense_domain.authorization import AuthorizationService, HiddenResource, PrincipalContext
from test_identity import HUMAN, NOW, PROD, TENANT, Audit, Authority, fixture, grant, scope


class Journal:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def correlation(self, scope, correlation_id, limit):
        self.calls.append((scope, correlation_id, limit))
        return self.rows


class AuditTimelineTests(unittest.TestCase):
    def setUp(self):
        self.correlation = uuid4()
        self.request = uuid4()
        self.scope = scope()
        self.context = PrincipalContext(HUMAN, TENANT, 1, 1, NOW + timedelta(minutes=1))
        self.audit = Audit()
        self.authority = Authority(fixture(roleGrants=[grant(role="auditReader")]))
        self.journal = Journal(())
        self.reader = TimelineReader(
            AuthorizationService(self.authority, self.audit), self.journal, lambda: NOW
        )

    def test_reconstructs_correlated_no_effect_trace_in_sequence_order(self):
        actions = [
            "sensitive_read",
            "policy_decision",
            "proposal_recorded",
            "approval_assessed",
            "synthetic_attempt",
            "synthetic_receipt",
        ]
        records = tuple(
            AuditRecord(
                event_id=uuid4(),
                scope=self.scope,
                correlation_id=self.correlation,
                sequence=i,
                recorded_at=NOW,
                actor_id=HUMAN,
                kind=kind,
                reference_id=uuid4(),
            )
            for i, kind in enumerate(actions, 1)
        )
        self.journal.rows = records[::-1]
        self.assertEqual(
            self.reader.read(self.context, self.scope, self.correlation, self.request), records
        )
        self.assertEqual(self.audit.events[0].correlation_id, self.request)
        self.assertEqual(self.journal.calls[0][:2], (self.scope, self.correlation))

    def test_hidden_audit_scope_and_append_failure_do_not_query_journal(self):
        with self.assertRaises(HiddenResource):
            self.reader.read(self.context, scope(PROD), self.correlation, self.request)
        self.audit.failed = True
        with self.assertRaisesRegex(RuntimeError, "AUDIT_UNAVAILABLE"):
            self.reader.read(self.context, self.scope, self.correlation, self.request)
        self.assertEqual(self.journal.calls, [])

    def test_bad_adapter_cannot_leak_mismatched_or_ambiguous_stream(self):
        item = AuditRecord(
            event_id=uuid4(),
            scope=self.scope,
            correlation_id=self.correlation,
            sequence=1,
            recorded_at=NOW,
            actor_id=HUMAN,
            kind="sensitive_read",
            reference_id=uuid4(),
        )
        for rows in (
            (item, item),
            (item.model_copy(update={"scope": scope(PROD)}),),
            (item.model_copy(update={"correlation_id": uuid4()}),),
        ):
            self.journal.rows = rows
            with self.assertRaisesRegex(InvalidTimeline, "^Audit timeline unavailable[.]$"):
                self.reader.read(self.context, self.scope, self.correlation, self.request)
