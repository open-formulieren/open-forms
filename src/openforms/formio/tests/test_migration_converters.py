from django.test import SimpleTestCase

from ..migration_converters import (
    ensure_licensplate_validate_pattern,
    ensure_postcode_validate_pattern,
    prevent_datetime_components_from_emptying_invalid_values,
)
from ..typing import Component


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
