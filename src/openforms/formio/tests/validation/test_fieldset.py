from django.test import SimpleTestCase, tag

from ...typing import FieldsetComponent
from .helpers import validate_formio_data


class FieldSetValidationTests(SimpleTestCase):

    @tag("gh-4068")
    def test_fieldset_doesnt_require_value(self):
        # Fieldset is a layout component, so there's never any data to validate
        component: FieldsetComponent = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "A field set",
            # don't ask me how, but somehow this got injected at some point. It's not
            # our new form builder, but it could be our own JS code in the backend in
            # src/openforms/js/components/formio_builder/WebformBuilder.js or they're
            # old forms that still suffer from #1724
            "validate": {
                "required": True,
            },
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Text field",
                },
            ],
        }

        is_valid, _ = validate_formio_data(component, {})

        self.assertTrue(is_valid)

    @tag("gh-4068")
    def test_hidden_fieldset_with_nested_required_fields(self):
        component: FieldsetComponent = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "A field set",
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Text field",
                    "validate": {"required": True},
                },
            ],
            "hidden": True,
            "conditional": {
                "show": True,
                "when": "missing",
                "eq": "never-triggered",
            },
        }

        is_valid, _ = validate_formio_data(component, {"textfield": ""})

        self.assertTrue(is_valid)

    def test_validate_nested_field_with_nested_key(self):
        component: FieldsetComponent = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "A field set",
            "components": [
                {
                    "type": "textfield",
                    "key": "fieldset.textfield",
                    "label": "Text field",
                    "validate": {"required": True},
                },
            ],
            "hidden": False,
        }

        is_valid, _ = validate_formio_data(component, {"fieldset": {"textfield": ""}})

        self.assertFalse(is_valid)
