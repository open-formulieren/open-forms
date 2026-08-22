from django.test import SimpleTestCase

from unittest_parametrize import ParametrizedTestCase, parametrize

from formio_types import AddressNL, TextField
from openforms.formio.typing import AddressNLComponent

from ...datastructures import FormioConfig
from .. import get_translated_custom_error_messages


class ComponentWithCustomErrorsTests(ParametrizedTestCase, SimpleTestCase):
    def test_no_translated_errors(self):
        config = FormioConfig(
            name="<test>",
            components=[
                {"key": "textField", "type": "textfield", "label": "Text Field"}
            ],
        )

        get_translated_custom_error_messages(config, "en")

        component = config["textField"]
        assert isinstance(component, TextField)
        self.assertIsNone(component.errors)

    def test_custom_errors_in_english(self):
        config = FormioConfig(
            name="<test>",
            components=[
                {
                    "key": "textField",
                    "type": "textfield",
                    "label": "Text Field",
                    "translatedErrors": {  # pyright: ignore[reportArgumentType]
                        "en": {
                            "pattern": "{{ field }} has the wrong pattern!!!",
                            "required": "{{ field }} is required!!!",
                            "maxLength": "{{ field }} is too long!!!",
                        },
                        "nl": {
                            "pattern": "{{ field }} komt niet overeen met de regex!!!",
                            "required": "{{ field }} is verplicht!!!",
                            "maxLength": "{{ field }} is te lang!!!",
                        },
                    },
                }
            ],
        )

        get_translated_custom_error_messages(config, "en")

        component = config["textField"]
        assert isinstance(component, TextField)
        assert component.errors is not None
        self.assertEqual(
            component.errors,
            {
                "pattern": "{{ field }} has the wrong pattern!!!",
                "required": "{{ field }} is required!!!",
                "maxLength": "{{ field }} is too long!!!",
            },
        )

    def test_existing_errors_not_overwritten(self):
        config = FormioConfig(
            name="<test>",
            components=[
                {
                    "key": "textField",
                    "type": "textfield",
                    "label": "Text Field",
                    "translatedErrors": {  # pyright: ignore[reportArgumentType]
                        "en": {
                            "pattern": "{{ field }} has the wrong pattern!!!",
                            "required": "{{ field }} is required!!!",
                            "maxLength": "{{ field }} is too long!!!",
                        },
                        "nl": {
                            "pattern": "{{ field }} komt niet overeen met de regex!!!",
                            "required": "{{ field }} is verplicht!!!",
                            "maxLength": "{{ field }} is te lang!!!",
                        },
                    },
                    "errors": {"pattern": "test"},  # pyright: ignore[reportArgumentType]
                }
            ],
        )

        get_translated_custom_error_messages(config, "en")

        component = config["textField"]
        assert isinstance(component, TextField)
        assert component.errors is not None
        self.assertEqual(component.errors, {"pattern": "test"})

    def test_addressnl_custom_error_messages(self):
        _component: AddressNLComponent = {
            "key": "addressNL",
            "type": "addressNL",
            "label": "Address",
            "deriveAddress": True,
            "openForms": {
                "components": {
                    "city": {
                        "validate": {"pattern": ""},
                        "translatedErrors": {
                            "en": {"pattern": "Custom city error"},
                            "nl": {"pattern": ""},
                        },
                    },
                    "postcode": {
                        "validate": {"pattern": ""},
                        "translatedErrors": {
                            "en": {"pattern": "Custom postcode error"},
                            "nl": {"pattern": ""},
                        },
                    },
                },
            },
        }
        config = FormioConfig(name="<test>", components=[_component])

        get_translated_custom_error_messages(config, "en")

        component = config["addressNL"]
        assert isinstance(component, AddressNL)
        assert component.open_forms is not None
        sub_components = component.open_forms.components
        assert sub_components is not None
        assert sub_components.city is not None
        assert sub_components.city.errors is not None
        assert sub_components.postcode is not None
        assert sub_components.postcode.errors is not None

        self.assertEqual(
            sub_components.city.errors,
            {"pattern": "Custom city error"},
        )
        self.assertEqual(
            sub_components.postcode.errors,
            {"pattern": "Custom postcode error"},
        )

    def test_addressnl_custom_error_messages_noop(self):
        _component: AddressNLComponent = {
            "key": "addressNL",
            "type": "addressNL",
            "label": "Address",
            "deriveAddress": True,
            "openForms": {
                "components": {
                    "city": {
                        "validate": {"pattern": ""},
                        "errors": {"pattern": "no touch"},  # pyright: ignore[reportAssignmentType]
                        "translatedErrors": {
                            "en": {"pattern": "Custom city error"},
                            "nl": {"pattern": ""},
                        },
                    },
                },
            },
        }
        config = FormioConfig(name="<test>", components=[_component])

        get_translated_custom_error_messages(config, "en")

        component = config["addressNL"]
        assert isinstance(component, AddressNL)
        assert component.open_forms is not None
        sub_components = component.open_forms.components
        assert sub_components is not None
        assert sub_components.city is not None
        assert sub_components.city.errors is not None
        self.assertEqual(sub_components.city.errors, {"pattern": "no touch"})

    @parametrize(
        "extensions_config",
        [
            None,
            {"components": {}},
            {"components": {"postcode": {}}},
            {"components": {"postcode": {"validate": {"pattern": ""}}}},
            {"components": {"postcode": {"translatedErrors": {}}}},
            {"components": {"postcode": {"translatedErrors": {"en": {}}}}},
        ],
    )
    def test_addressnl_custom_error_messages_missing_config(self, extensions_config):
        _component: AddressNLComponent = {
            "key": "addressNL",
            "type": "addressNL",
            "label": "Address",
            "deriveAddress": True,
            "openForms": extensions_config,
        }
        config = FormioConfig(name="<test>", components=[_component])

        get_translated_custom_error_messages(config, "en")

        component = config["addressNL"]
        assert isinstance(component, AddressNL)
        # assert that no translation is set
        errors = None
        try:
            errors = component.open_forms.components.postcode.errors  # type: ignore
        except AttributeError:
            pass
        if errors is not None:
            self.fail("errors should not have been set")
