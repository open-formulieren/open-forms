from django.test import SimpleTestCase

from ..migration_converters import (
    ensure_addressnl_has_deriveAddress,
    ensure_licensplate_validate_pattern,
    ensure_postcode_validate_pattern,
    fix_multiple_empty_default_value,
    prevent_datetime_components_from_emptying_invalid_values,
)
from ..typing import AddressNLComponent, Component


class LicensePlateTests(SimpleTestCase):
    def test_noop(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licenseplate",
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"  # type: ignore
            },
        }

        changed = ensure_licensplate_validate_pattern(component)

        self.assertFalse(changed)


class PostCodeTests(SimpleTestCase):
    def test_noop(self):
        component: Component = {
            "type": "postcode",
            "key": "postcode",
            "validate": {
                "pattern": r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"  # type: ignore
            },
        }

        changed = ensure_postcode_validate_pattern(component)

        self.assertFalse(changed)


class DatetimeTests(SimpleTestCase):
    def test_update(self):
        component: Component = {
            "type": "datetime",
            "key": "datetime",
        }

        changed = prevent_datetime_components_from_emptying_invalid_values(component)

        self.assertTrue(changed)
        self.assertTrue(component["customOptions"]["allowInvalidPreload"])


class SelectTests(SimpleTestCase):
    def test_no_multiple_noop(self):
        component: Component = {
            "type": "select",
            "key": "select",
            "label": "Select",
        }
        changed = fix_multiple_empty_default_value(component)
        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "multiple": True,
            "defaultValue": [],
        }
        changed = fix_multiple_empty_default_value(component)
        self.assertFalse(changed)

    def test_default_value_changed(self):
        component: Component = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "multiple": True,
            "defaultValue": [""],
        }
        changed = fix_multiple_empty_default_value(component)
        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])


class AddressNLTests(SimpleTestCase):
    def test_existing_derive_address(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Required AddressNL",
            "deriveAddress": False,
        }

        changed = ensure_addressnl_has_deriveAddress(component)

        self.assertFalse(changed)

    def test_missing_derive_address(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Required AddressNL",
        }

        changed = ensure_addressnl_has_deriveAddress(component)

        self.assertTrue(changed)
        self.assertFalse(component["deriveAddress"])
