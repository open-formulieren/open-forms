from django.test import SimpleTestCase

import msgspec

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class FallbackBehaviourTests(SimpleTestCase):
    def test_unknown_component_passthrough(self):
        # TODO: this should *not* pass when all components are implemented, it's a
        # temporary compatibility layer
        component: Component = {
            "type": "unknown-i-do-not-exist",
            "key": "foo",
            "label": "Fallback",
        }
        data: JSONValue = {"value": ["weird", {"data": "structure"}]}

        with self.assertRaises(msgspec.ValidationError):
            validate_formio_data(component, data)

    def test_nested_keys_and_fields_being_required(self):
        component: Component = {
            "type": "textfield",
            "key": "nested.field",
            "label": "Nested data",
            "validate": {"required": True},
        }

        is_valid, errors = validate_formio_data(component, {})

        self.assertFalse(is_valid)
        error = extract_error(errors, "nested")
        self.assertEqual(error.code, "required")
