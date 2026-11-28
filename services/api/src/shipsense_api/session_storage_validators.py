"""Inert Decision 0012 collection definitions; never applied by the application."""

from bson import Int64

from shipsense_api.session_storage_codec import (
    ACCOUNT_COLLECTION,
    AUDIT_COLLECTION,
    MAX_INT64,
    SESSION_COLLECTION,
)

_UUID = r"\A[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\z"


def _long(minimum: int, *, nullable: bool = False) -> dict[str, object]:
    return {
        "bsonType": ["null", "long"] if nullable else "long",
        "minimum": Int64(minimum),
        "maximum": Int64(MAX_INT64),
    }


def _string(*, pattern: str) -> dict[str, object]:
    return {"bsonType": "string", "pattern": pattern}


def _literals(*values: str) -> dict[str, object]:
    return {"bsonType": "string", "enum": list(values)}


def _strict(
    properties: dict[str, object], *, expr: object = None, alternatives: object = None
) -> dict[str, object]:
    schema = {
        "bsonType": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }
    if alternatives is not None:
        schema["oneOf"] = alternatives
    validator: dict[str, object] = {"$jsonSchema": schema}
    if expr is not None:
        validator["$expr"] = expr
    return {"validator": validator, "validationLevel": "strict", "validationAction": "error"}


def collection_validation_options() -> dict[str, dict[str, object]]:
    """Return fresh MongoDB create/verify metadata, with no database handle."""
    version = {"bsonType": "int", "enum": [1]}
    session_time_bounds = {
        "$and": [
            {"$lte": ["$created_at", "$last_activity_at"]},
            {"$lt": ["$last_activity_at", "$absolute_expires_at"]},
            {"$lte": [{"$subtract": ["$absolute_expires_at", "$created_at"]}, 900]},
            {"$lt": ["$last_activity_at", "$idle_expires_at"]},
            {"$lte": [{"$subtract": ["$idle_expires_at", "$last_activity_at"]}, 600]},
            {"$or": [{"$eq": ["$revoked_at", None]}, {"$gte": ["$revoked_at", "$created_at"]}]},
        ]
    }
    return {
        SESSION_COLLECTION: _strict(
            {
                "_id": _string(pattern=r"\A[a-f0-9]{64}\z"),
                "schema_version": version.copy(),
                "fence": _long(1),
                "account_id": _string(pattern=_UUID),
                "authentication_epoch": _long(1),
                "revision": _long(1),
                "created_at": _long(0),
                "last_activity_at": _long(0),
                "absolute_expires_at": _long(0),
                "idle_expires_at": _long(0),
                "revoked_at": _long(0, nullable=True),
            },
            expr=session_time_bounds,
        ),
        ACCOUNT_COLLECTION: _strict(
            {
                "_id": _string(pattern=_UUID),
                "schema_version": version.copy(),
                "fence": _long(1),
                "authentication_epoch": _long(1),
                "revision": _long(1),
                "status": _literals("active", "suspended", "archived"),
            }
        ),
        AUDIT_COLLECTION: _strict(
            {
                "_id": _string(pattern=_UUID),
                "schema_version": version.copy(),
                "partition": _literals("authentication"),
                "actor": _literals("shipsense-bff"),
                "action": _literals("session.resolve", "session.revoke"),
                "outcome": _literals("allowed", "denied", "revoked"),
                "recorded_at": _long(0),
                "correlation_id": _string(pattern=r"\A[A-Za-z0-9_-]{1,64}\z"),
            },
            alternatives=[
                {
                    "properties": {
                        "action": {"enum": ["session.resolve"]},
                        "outcome": {"enum": ["allowed", "denied"]},
                    }
                },
                {
                    "properties": {
                        "action": {"enum": ["session.revoke"]},
                        "outcome": {"enum": ["revoked"]},
                    }
                },
            ],
        ),
    }
