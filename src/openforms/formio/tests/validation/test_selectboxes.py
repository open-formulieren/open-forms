from django.test import SimpleTestCase

from hypothesis import given, strategies as st

from openforms.formio.constants import DataSrcOptions
from openforms.typing import JSONValue

from ...typing import SelectBoxesComponent
from .helpers import extract_error, validate_formio_data


class SelectboxesValidationTests(SimpleTestCase):

    def test_selectboxes_required_validation(self):
        component: SelectBoxesComponent = {
            "type": "selectboxes",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
                {"value": "c", "label": "C"},
            ],
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": None}, "null"),
            # verified with https://formio.github.io/formio.js/app/builder.html -
            # selectboxes being required means that at least one option must be checked
            ({"foo": {"a": False, "b": False, "c": False}}, "required"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_optional_selectboxes(self):
        # hypothetical input - it appears that the Formio.js SDK always provides the
        # nested object, whether required or not.
        # See also :func:`openforms.formio.utils.get_component_empty_value` which
        # special cases the selectboxes.
        component: SelectBoxesComponent = {
            "type": "selectboxes",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
                {"value": "c", "label": "C"},
            ],
        }

        valid_values = [
            # empty/None... maybe we should block those? I think ultimately they come
            # down to the bottom case anyway...
            {},
            {"foo": None},
            # this is what the SDK/frontend produces
            {"foo": {"a": False, "b": False, "c": False}},
        ]
        for data in valid_values:
            with self.subTest(valid_value=data):
                is_valid, _ = validate_formio_data(component, data)

                self.assertTrue(is_valid)

    @given(required=st.booleans())
    def test_all_options_must_be_specified(self, required: bool):
        # Each value needs to be specified with a True/False value
        component: SelectBoxesComponent = {
            "type": "selectboxes",
            "key": "foo",
            "label": "Test",
            "validate": {"required": required},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        is_valid, errors = validate_formio_data(component, {"foo": {"a": True}})

        self.assertFalse(is_valid)
        error = extract_error(errors["foo"], "b")
        self.assertEqual(error.code, "required")

    def test_additional_options_are_ignored(self):
        # Each value needs to be specified with a True/False value
        component: SelectBoxesComponent = {
            "type": "selectboxes",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        is_valid, _ = validate_formio_data(
            component, {"foo": {"a": True, "b": False, "c": None}}
        )

        self.assertTrue(is_valid)

    def test_validate_min_checked(self):
        component: SelectBoxesComponent = {
            "type": "selectboxes",
            "key": "foo",
            "label": "Test",
            "validate": {
                "required": False,
                "minSelectedCount": 2,
            },
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        data: JSONValue = {"foo": {"a": True, "b": False}}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "min_selected_count")

    def test_validate_max_checked(self):
        component: SelectBoxesComponent = {
            "type": "selectboxes",
            "key": "foo",
            "label": "Test",
            "validate": {
                "required": False,
                "maxSelectedCount": 1,
            },
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        data: JSONValue = {"foo": {"a": True, "b": True}}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "max_selected_count")
