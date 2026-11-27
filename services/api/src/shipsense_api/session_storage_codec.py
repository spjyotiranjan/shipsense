"""Decision 0012 BSON boundary; no driver client, transactions, or collection setup."""

from collections.abc import Mapping
from uuid import UUID

from bson import Int64
from pydantic import ValidationError
from shipsense_domain.sessions import SessionAccount, SessionAudit, SessionRecord

SESSION_COLLECTION = "auth_sessions"
ACCOUNT_COLLECTION = "auth_accounts"
AUDIT_COLLECTION = "auth_session_audit"
MAX_INT64 = (1 << 63) - 1
_ENVELOPE = {"_id", "schema_version", "fence"}
_SESSION_TIMES = {"created_at", "last_activity_at", "absolute_expires_at", "idle_expires_at"}
_COUNTERS = {"authentication_epoch", "revision"}


class InvalidStorageRecord(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid session storage record.")


def _uuid(value: object) -> UUID:
    if type(value) is str:
        try:
            identifier = UUID(value)
            if str(identifier) == value:
                return identifier
        except ValueError:
            pass
    raise InvalidStorageRecord()


def _int64(value: object, minimum: int = 1) -> int:
    if type(value) is not Int64 or not minimum <= value <= MAX_INT64:
        raise InvalidStorageRecord()
    return int(value)


def _validate_envelope(document: Mapping[str, object], fields: set[str]) -> None:
    if set(document) != _ENVELOPE | fields:
        raise InvalidStorageRecord()
    version = document["schema_version"]
    if type(version) is not int or version != 1:
        raise InvalidStorageRecord()
    _int64(document["fence"])


def decode_session(document: Mapping[str, object], expected_digest: str) -> SessionRecord:
    _validate_envelope(document, _COUNTERS | _SESSION_TIMES | {"account_id", "revoked_at"})
    digest = document["_id"]
    if type(digest) is not str or digest != expected_digest:
        raise InvalidStorageRecord()
    revoked = document["revoked_at"]
    values: dict[str, object] = {name: _int64(document[name], 0) for name in _SESSION_TIMES}
    values.update(
        handle_digest=digest,
        account_id=_uuid(document["account_id"]),
        revoked_at=None if revoked is None else _int64(revoked, 0),
    )
    values.update({name: _int64(document[name]) for name in _COUNTERS})
    try:
        return SessionRecord.model_validate(values)
    except ValidationError:
        raise InvalidStorageRecord() from None


def decode_account(document: Mapping[str, object], expected_account_id: UUID) -> SessionAccount:
    _validate_envelope(document, _COUNTERS | {"status"})
    account_id = _uuid(document["_id"])
    if account_id != expected_account_id:
        raise InvalidStorageRecord()
    try:
        return SessionAccount.model_validate(
            dict(account_id=account_id, status=document["status"])
            | {name: _int64(document[name]) for name in _COUNTERS}
        )
    except ValidationError:
        raise InvalidStorageRecord() from None


def encode_audit(event: SessionAudit) -> dict[str, object]:
    try:
        checked = SessionAudit.model_validate(event.model_dump())
    except ValidationError:
        raise InvalidStorageRecord() from None
    if checked.recorded_at > MAX_INT64:
        raise InvalidStorageRecord()
    return {
        "_id": str(checked.event_id),
        "schema_version": 1,
        "partition": checked.partition,
        "actor": checked.actor,
        "action": checked.action,
        "outcome": checked.outcome,
        "recorded_at": Int64(checked.recorded_at),
        "correlation_id": checked.correlation_id,
    }
