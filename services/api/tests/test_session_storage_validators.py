import unittest

from bson import BSON, Int64
from shipsense_api.session_storage_codec import (
    ACCOUNT_COLLECTION,
    AUDIT_COLLECTION,
    MAX_INT64,
    SESSION_COLLECTION,
)
from shipsense_api.session_storage_validators import collection_validation_options


class StorageValidatorTests(unittest.TestCase):
    def test_only_fixed_collections_with_strict_error_on_any_write(self):
        options = BSON.encode(collection_validation_options()).decode()
        self.assertEqual(set(options), {SESSION_COLLECTION, ACCOUNT_COLLECTION, AUDIT_COLLECTION})
        for result in options.values():
            self.assertEqual(set(result), {"validator", "validationLevel", "validationAction"})
            self.assertEqual(result["validationLevel"], "strict")
            self.assertEqual(result["validationAction"], "error")
            schema = result["validator"]["$jsonSchema"]
            self.assertEqual(set(schema["required"]), set(schema["properties"]))
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(
                schema["properties"]["schema_version"], {"bsonType": "int", "enum": [1]}
            )

    def test_session_longs_are_bounded_and_audit_has_no_session_fields(self):
        options = BSON.encode(collection_validation_options()).decode()
        for name in (SESSION_COLLECTION, ACCOUNT_COLLECTION):
            props = options[name]["validator"]["$jsonSchema"]["properties"]
            for field in ("fence", "revision", "authentication_epoch"):
                self.assertEqual(
                    props[field],
                    {"bsonType": "long", "minimum": Int64(1), "maximum": Int64(MAX_INT64)},
                )
                self.assertIs(type(props[field]["maximum"]), Int64)
        session = options[SESSION_COLLECTION]["validator"]
        self.assertIn("$expr", session)
        self.assertEqual(
            session["$jsonSchema"]["properties"]["revoked_at"],
            {"bsonType": ["null", "long"], "minimum": Int64(0), "maximum": Int64(MAX_INT64)},
        )
        audit = options[AUDIT_COLLECTION]["validator"]["$jsonSchema"]
        self.assertEqual(
            set(audit["properties"]),
            {
                "_id",
                "schema_version",
                "partition",
                "actor",
                "action",
                "outcome",
                "recorded_at",
                "correlation_id",
            },
        )
        self.assertEqual(
            audit["oneOf"],
            [
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
        )

    def test_callers_cannot_change_next_manifest(self):
        options = collection_validation_options()
        options[SESSION_COLLECTION].clear()
        self.assertEqual(
            collection_validation_options()[SESSION_COLLECTION]["validationAction"], "error"
        )
