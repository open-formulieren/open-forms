from django.test import SimpleTestCase, tag

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import JSONObject

from ...service import build_serializer
from ...typing import EditGridComponent
from .helpers import validate_formio_data


class EditGridValidationTests(SimpleTestCase):
    """
    Test validations on the edit grid and its nested components.
    """

    def test_nested_fields_are_validated(self):
        component: EditGridComponent = {
            "type": "editgrid",
            "key": "parent",
            "label": "Repeating group",
            "components": [
                {
                    "type": "textfield",
                    "key": "nested",
                    "label": "Nested text field",
                    "validate": {
                        "required": True,
                    },
                }
            ],
        }
        data: JSONObject = {
            "parent": [
                {
                    "nested": "foo",
                },
                {
                    "nested": "",
                },
                {},
            ],
        }

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)

        assert isinstance(errors, dict)
        assert "parent" in errors
        nested = errors["parent"]
        assert isinstance(nested, dict)

        with self.subTest("Item at index 0"):
            self.assertNotIn(0, nested)

        with self.subTest("Item at index 1"):
            self.assertIn(1, nested)
            _errors = nested[1]
            self.assertIsInstance(_errors, dict)
            self.assertIn("nested", _errors)
            self.assertEqual(len(_errors["nested"]), 1)
            self.assertEqual(_errors["nested"][0].code, "blank")

        with self.subTest("Item at index 2"):
            self.assertIn(2, nested)
            _errors = nested[2]
            self.assertIsInstance(_errors, dict)
            self.assertIn("nested", _errors)
            self.assertEqual(len(_errors["nested"]), 1)
            self.assertEqual(_errors["nested"][0].code, "required")

    def test_editgrids_own_validations(self):
        component: EditGridComponent = {
            "type": "editgrid",
            "key": "parent",
            "label": "Repeating group",
            "components": [
                {
                    "type": "textfield",
                    "key": "nested",
                    "label": "Nested text field",
                }
            ],
            "validate": {
                "required": True,
                "maxLength": 2,
            },
        }

        with self.subTest("Required values missing"):
            data: JSONObject = {}

            is_valid, errors = validate_formio_data(component, data)

            self.assertFalse(is_valid)

            assert isinstance(errors, dict)
            assert "parent" in errors
            nested = errors["parent"]

            self.assertIsInstance(nested, list)
            err_code = nested[0].code
            self.assertEqual(err_code, "required")

        with self.subTest("Max length exceeded"):
            data: JSONObject = {
                "parent": [
                    {"nested": "foo"},
                    {"nested": "bar"},
                    {"nested": "bax"},
                ]
            }

            is_valid, errors = validate_formio_data(component, data)

            self.assertFalse(is_valid)

            assert isinstance(errors, dict)
            assert "parent" in errors
            nested = errors["parent"]

            self.assertIsInstance(nested, list)
            err_code = nested[0].code
            self.assertEqual(err_code, "max_length")

    def test_valid_configuration_nested_field_not_present_in_top_level_serializer(self):
        """
        Test that the nested components in edit grid are not processed in a generic way.

        They are a blueprint for items in an array, so when iterating over all
        components (recursively), they may not show up as standalone components.
        """
        component: EditGridComponent = {
            "type": "editgrid",
            "key": "toplevel",
            "label": "Repeating group",
            "components": [
                {
                    "type": "textfield",
                    "key": "nested",
                    "label": "Required textfield",
                    "validate": {"required": True},
                }
            ],
        }
        data: JSONObject = {
            "toplevel": [{"nested": "i am valid"}],
        }
        context = {"submission": SubmissionFactory.build()}

        serializer = build_serializer(
            components=[component], data=data, context=context
        )

        with self.subTest("serializer validity"):
            self.assertTrue(serializer.is_valid())

        top_level_fields = serializer.fields
        with self.subTest("top level fields"):
            self.assertIn("toplevel", top_level_fields)
            self.assertNotIn("nested", top_level_fields)

        with self.subTest("nested fields"):
            nested_fields = top_level_fields["toplevel"].child.fields  # type: ignore

            self.assertIn("nested", nested_fields)
            self.assertNotIn("toplevel", nested_fields)

    @tag("gh-4068")
    def test_optional_editgrid(self):
        component: EditGridComponent = {
            "type": "editgrid",
            "key": "optionalRepeatingGroup",
            "label": "Optional repeating group",
            "validate": {"required": False},
            "components": [
                {
                    "type": "textfield",
                    "key": "optionalTextfield",
                    "label": "Optional Text field",
                    "validate": {"required": False},
                }
            ],
        }

        is_valid, errors = validate_formio_data(
            component,
            {"optionalRepeatingGroup": []},
        )

        self.assertTrue(is_valid)
