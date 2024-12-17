from django.test import SimpleTestCase

from referencing.exceptions import Unresolvable

from ..json_schema import (
    get_missing_required_paths,
    iter_json_schema_paths,
    json_schema_matches,
)

JSON_SCHEMA_NO_SPEC = {"type": "object", "properties": {"prop": {"type": "string"}}}

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
                "two_types": {
                    "type": ["string", "number"],
                },
            },
        },
    },
}

JSON_SCHEMA_NO_TYPE = {
    "$id": "noise-complaint.schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "additionalProperties": False,
    "properties": {
        "complaintDescription": {"type": "string"},
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
        "phoneNumber": {"$ref": "#/definitions/phoneNumber"},
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
        "phoneNumber": {
            "type": "number",
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

JSON_SCHEMA_REQUIRED_PATHS = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "a": {"type": "string"},
        "b": {
            "type": "object",
            "properties": {
                "c": {"type": "string"},
                "d": {
                    "type": "object",
                    "properties": {
                        "e": {"type": "string"},
                        "f": {"type": "string"},
                    },
                    "required": ["e"],
                },
            },
            "required": ["c", "d"],
        },
    },
    "required": ["a", "b"],
}

# "a" not required, but "a.b" is:
JSON_SCHEMA_DEEP_REQUIRED = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "a": {
            "type": "object",
            "required": ["b"],
            "properties": {
                "b": {"type": "string"},
                "c": {"type": "string"},
            },
        }
    },
}


class IterJsonSchemaTests(SimpleTestCase):
    """Test cases to assert the JSON Schemas are correctly iterated over.

    The first path element being the root one, it is not included as it could
    simply be tested as ``([], CURRENT_SCHEMA_TESTED)``.
    """

    def test_no_spec_default(self):
        try:
            list(iter_json_schema_paths(JSON_SCHEMA_NO_SPEC))
        except Exception as e:
            raise self.failureException("Unexpected exception") from e

    def test_iter_json_schema_no_refs(self):
        paths_list = [
            (path.segments, schema)
            for path, schema in iter_json_schema_paths(JSON_SCHEMA_NO_REFS)
        ]

        self.assertEqual(
            paths_list[1:],
            [
                (["complaintDescription"], {"type": "string"}),
                (["measuredDecibels"], {"type": "array", "items": {"type": "number"}}),
                (
                    ["complainant"],
                    {
                        "properties": {
                            "first.name": {"type": "string"},
                            "last.name": {"type": "string"},
                            "two_types": {"type": ["string", "number"]},
                        },
                        "type": "object",
                    },
                ),
                (["complainant", "first.name"], {"type": "string"}),
                (["complainant", "last.name"], {"type": "string"}),
                (["complainant", "two_types"], {"type": ["string", "number"]}),
            ],
        )

    def test_iter_json_schema_no_type(self):
        paths_list = [
            (path.segments, schema)
            for path, schema in iter_json_schema_paths(JSON_SCHEMA_NO_TYPE)
        ]

        self.assertEqual(
            paths_list[1:],
            [
                (["complaintDescription"], {"type": "string"}),
            ],
        )

    def test_iter_json_schema_refs(self):
        paths_list = [
            (path.segments, schema)
            for path, schema in iter_json_schema_paths(JSON_SCHEMA_REFS)
        ]

        self.assertEqual(
            paths_list[1:],
            [
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
                (["phoneNumber"], {"type": "number"}),
            ],
        )

    def test_iter_json_schema_nested_refs(self):
        paths_list = [
            (path.segments, schema)
            for path, schema in iter_json_schema_paths(JSON_SCHEMA_NESTED_REFS)
        ]

        self.assertEqual(
            paths_list[1:],
            [
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
        with self.assertRaises(Unresolvable):
            list(iter_json_schema_paths(JSON_SCHEMA_UNKOWN_REF, fail_fast=True))

        paths_list = [
            (path.segments, schema)
            for path, schema in iter_json_schema_paths(
                JSON_SCHEMA_UNKOWN_REF, fail_fast=False
            )
        ]

        self.assertEqual(paths_list[1][0], ["invalid"])
        self.assertEqual(paths_list[1][1].uri, "#/invalidref")

    def test_iter_json_schema_external_ref(self):
        with self.assertRaises(Unresolvable):
            list(iter_json_schema_paths(JSON_SCHEMA_EXTERNAL_REF, fail_fast=True))

        paths_list = [
            (path.segments, schema)
            for path, schema in iter_json_schema_paths(
                JSON_SCHEMA_EXTERNAL_REF, fail_fast=False
            )
        ]

        self.assertEqual(paths_list[1][0], ["external"])
        self.assertEqual(
            paths_list[1][1].uri, "http://example.com/external-schema.json"
        )


class RequiredJsonSchemaPathsTests(SimpleTestCase):
    """Test cases to assert required paths are correctly picked up when iterating over JSON Schemas

    (``IterJsonSchemaTests`` only made assertions on the returned paths).
    """

    def test_required_json_schema_paths(self):
        required_paths = [
            path.segments
            for path, _ in iter_json_schema_paths(JSON_SCHEMA_REQUIRED_PATHS)
            if path.required
        ]

        self.assertEqual(
            required_paths, [["a"], ["b"], ["b", "c"], ["b", "d"], ["b", "d", "e"]]
        )


class MissingRequiredPathsTests(SimpleTestCase):
    """Test cases to assert missing required paths are picked up."""

    def test_no_missing_required_paths(self):

        with self.subTest("top level"):
            missing_paths = get_missing_required_paths(
                JSON_SCHEMA_REQUIRED_PATHS, [["a"], ["b"]]
            )

            self.assertEqual(missing_paths, [])

        with self.subTest("nested paths"):
            missing_paths = get_missing_required_paths(
                JSON_SCHEMA_REQUIRED_PATHS, [["a"], ["b", "c"], ["b", "d", "e"]]
            )

            self.assertEqual(missing_paths, [])

    def test_missing_required_paths(self):

        with self.subTest("Missing 'a'"):
            missing_paths = get_missing_required_paths(
                JSON_SCHEMA_REQUIRED_PATHS, [["b"]]
            )

            self.assertEqual(missing_paths, [["a"]])

        with self.subTest("Missing 'b'"):
            missing_paths = get_missing_required_paths(
                JSON_SCHEMA_REQUIRED_PATHS, [["a"]]
            )

            self.assertEqual(
                missing_paths, [["b"], ["b", "c"], ["b", "d"], ["b", "d", "e"]]
            )

        with self.subTest("Missing 'c'"):
            missing_paths = get_missing_required_paths(
                JSON_SCHEMA_REQUIRED_PATHS, [["a"], ["b", "d"]]
            )

            self.assertEqual(missing_paths, [["b", "c"]])

        with self.subTest("Missing 'e'"):
            missing_paths = get_missing_required_paths(
                JSON_SCHEMA_REQUIRED_PATHS, [["a"], ["b", "c"], ["b", "d", "f"]]
            )

            self.assertEqual(missing_paths, [["b", "d", "e"]])

    def test_required_path_deep(self):
        """Test that "a.b" is not marked as required if "a" is not provided."""

        missing_paths = get_missing_required_paths(JSON_SCHEMA_DEEP_REQUIRED, [])
        self.assertEqual(missing_paths, [])


class MatchesJsonShemaTests(SimpleTestCase):
    def test_json_schema_matches(self):
        with self.subTest("no type in variable"):
            variable_schema = {"unrelated": "property"}
            target_schema = {"type": "string"}

            self.assertFalse(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("no type in target"):
            variable_schema = {"whatever": "in there"}
            target_schema = {"no": "type"}

            self.assertTrue(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("array of types matches"):
            variable_schema = {"type": ["string", "number"]}
            target_schema = {"type": ["number", "string"]}

            self.assertTrue(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("array of types is subset"):
            variable_schema = {"type": ["string", "number"]}
            target_schema = {"type": ["number", "string", "object"]}

            self.assertTrue(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("array of types is not subset"):
            variable_schema = {"type": ["string", "array"]}
            target_schema = {"type": ["number", "string", "object"]}

            self.assertFalse(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("target has format, variable does not"):
            variable_schema = {"type": "string"}
            target_schema = {"type": "string", "format": "email"}

            self.assertTrue(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("variable has format, target does not"):
            variable_schema = {"type": "string", "format": "email"}
            target_schema = {"type": "string"}

            self.assertTrue(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("target and variable matches format"):
            variable_schema = {"type": "string", "format": "email"}
            target_schema = {"type": "string", "format": "email"}

            self.assertTrue(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )

        with self.subTest("target and variable does not match format"):
            variable_schema = {"type": "string", "format": "ipv4"}
            target_schema = {"type": "string", "format": "email"}

            self.assertFalse(
                json_schema_matches(
                    variable_schema=variable_schema, target_schema=target_schema
                )
            )
