from django.test import SimpleTestCase

from referencing.exceptions import Unresolvable

from ..json_schema import InvalidReference, iter_json_schema

JSON_SCHEMA_NO_REFS = {
    "$id": "noise-complaint.schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "complaintDescription": {"type": "string"},
        "measuredDecibels": {"type": "array", "items": {"type": "number"}},
        "complainant": {
            "type": "object",
            "properties": {
                "first.name": {"type": "string"},
                "last.name": {"type": "string"},
            },
        },
    },
}

JSON_SCHEMA_REFS = {
    "$id": "noise-complaint.schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "complainant": {"$ref": "#/definitions/person"},
        "noisyAddress": {"$ref": "#/definitions/address"},
    },
    "definitions": {
        "person": {
            "type": "object",
            "properties": {
                "first.name": {"type": "string"},
                "last.name": {"type": "string"},
            },
        },
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
            },
        },
    },
}


JSON_SCHEMA_NESTED_REFS = {
    "$id": "noise-complaint.schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Noise complaint example V2",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "complainant": {"$ref": "#/definitions/person"},
    },
    "definitions": {
        "person": {
            "type": "object",
            "properties": {
                "residence": {"$ref": "#/definitions/address"},
            },
        },
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
            },
        },
    },
}

JSON_SCHEMA_UNKOWN_REF = {
    "$id": "noise-complaint.schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "invalid": {"$ref": "#/invalidref"},
    },
}

JSON_SCHEMA_EXTERNAL_REF = {
    "$id": "noise-complaint.schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "external": {"$ref": "http://example.com/external-schema.json"},
    },
}


class IterJsonSchemaTests(SimpleTestCase):

    def test_iter_json_schema_no_refs(self):
        paths_list = list(iter_json_schema(JSON_SCHEMA_NO_REFS))

        self.assertListEqual(
            paths_list,
            [
                ([], JSON_SCHEMA_NO_REFS),
                (["complaintDescription"], {"type": "string"}),
                (["measuredDecibels"], {"type": "array", "items": {"type": "number"}}),
                (
                    ["complainant"],
                    {
                        "properties": {
                            "first.name": {"type": "string"},
                            "last.name": {"type": "string"},
                        },
                        "type": "object",
                    },
                ),
                (["complainant", "first.name"], {"type": "string"}),
                (["complainant", "last.name"], {"type": "string"}),
            ],
        )

    def test_iter_json_schema_refs(self):
        paths_list = list(iter_json_schema(JSON_SCHEMA_REFS))

        self.assertListEqual(
            paths_list,
            [
                ([], JSON_SCHEMA_REFS),
                (
                    ["complainant"],
                    {
                        "properties": {
                            "first.name": {"type": "string"},
                            "last.name": {"type": "string"},
                        },
                        "type": "object",
                    },
                ),
                (["complainant", "first.name"], {"type": "string"}),
                (["complainant", "last.name"], {"type": "string"}),
                (
                    ["noisyAddress"],
                    {
                        "properties": {
                            "street": {"type": "string"},
                        },
                        "type": "object",
                    },
                ),
                (["noisyAddress", "street"], {"type": "string"}),
            ],
        )

    def test_iter_json_schema_nested_refs(self):
        paths_list = list(iter_json_schema(JSON_SCHEMA_NESTED_REFS))

        self.assertListEqual(
            paths_list,
            [
                ([], JSON_SCHEMA_NESTED_REFS),
                (
                    ["complainant"],
                    {
                        "properties": {"residence": {"$ref": "#/definitions/address"}},
                        "type": "object",
                    },
                ),
                (
                    ["complainant", "residence"],
                    {"properties": {"street": {"type": "string"}}, "type": "object"},
                ),
                (["complainant", "residence", "street"], {"type": "string"}),
            ],
        )

    def test_iter_json_schema_unknown_ref(self):
        self.assertRaises(
            Unresolvable,
            lambda: list(iter_json_schema(JSON_SCHEMA_UNKOWN_REF, fail_fast=True)),
        )

        paths_list = list(iter_json_schema(JSON_SCHEMA_UNKOWN_REF, fail_fast=False))

        self.assertEqual(
            paths_list,
            [
                ([], JSON_SCHEMA_UNKOWN_REF),
                (["invalid"], InvalidReference("#/invalidref")),
            ],
        )

    def test_iter_json_schema_external_ref(self):
        self.assertRaises(
            Unresolvable,
            lambda: list(iter_json_schema(JSON_SCHEMA_EXTERNAL_REF, fail_fast=True)),
        )

        paths_list = list(iter_json_schema(JSON_SCHEMA_EXTERNAL_REF, fail_fast=False))

        self.assertEqual(
            paths_list,
            [
                ([], JSON_SCHEMA_EXTERNAL_REF),
                (
                    ["external"],
                    InvalidReference("http://example.com/external-schema.json"),
                ),
            ],
        )
