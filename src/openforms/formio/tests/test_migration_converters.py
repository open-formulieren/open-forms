from django.test import SimpleTestCase

from ..migration_converters import (
    ensure_addressnl_has_deriveAddress,
    ensure_licensplate_validate_pattern,
    ensure_map_has_interactions,
    ensure_postcode_validate_pattern,
    fix_empty_default_value,
    fix_file_default_value,
    fix_multiple_empty_default_value,
    prevent_datetime_components_from_emptying_invalid_values,
)
from ..typing import AddressNLComponent, Component, MapComponent


class LicensePlateTests(SimpleTestCase):
    def test_noop(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"  # type: ignore
            },
        }

        changed = ensure_licensplate_validate_pattern(component)

        self.assertFalse(changed)

    def test_multiple_noop(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "licenseplate",
            "key": "licensePlate",
            "label": "Licenseplate",
            "defaultValue": ["foo", None, "bar"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["foo", "", "bar"])


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

    def test_null_default_value(self):
        component: Component = {
            "type": "postcode",
            "key": "postcode",
            "validate": {
                "pattern": r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"  # type: ignore
            },
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_null_default_value_multiple(self):
        component: Component = {
            "type": "postcode",
            "key": "postcode",
            "validate": {
                "pattern": r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"  # type: ignore
            },
            "multiple": True,
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])


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

    def test_null_default_value(self):
        component: Component = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_null_default_value_multiple(self):
        component: Component = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "multiple": True,
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])


class TextTests(SimpleTestCase):
    def test_multiple_noop(self):
        component: Component = {
            "type": "textfield",
            "key": "textField",
            "label": "Text field",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "textfield",
            "key": "textField",
            "label": "Text field",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "textfield",
            "key": "textField",
            "label": "Text field",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "textfield",
            "key": "textField",
            "label": "Text field",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_in_array_changed(self):
        component: Component = {
            "type": "textfield",
            "key": "textField",
            "label": "Text field",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "textfield",
            "key": "textField",
            "label": "Text field",
            "defaultValue": ["foo", None, "bar"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["foo", "", "bar"])

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "key": "textField",
            "label": "Text Field",
            "type": "textfield",
            "multiple": True,
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])


class EmailTests(SimpleTestCase):
    def test_multiple_noop(self):
        component: Component = {
            "type": "email",
            "key": "eMailadres",
            "label": "Emailadres",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "email",
            "key": "eMailadres",
            "label": "Emailadres",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "email",
            "key": "eMailadres",
            "label": "Emailadres",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "email",
            "key": "eMailadres",
            "label": "Emailadres",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "type": "email",
            "key": "eMailadres",
            "label": "Emailadres",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "email",
            "key": "eMailadres",
            "label": "Emailadres",
            "defaultValue": ["foo", None, "bar"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["foo", "", "bar"])


class TimeTests(SimpleTestCase):
    def test_multiple_noop(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Time",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Time",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Time",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Time",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Time",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Time",
            "defaultValue": ["11:11", None, "22:22"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["11:11", "", "22:22"])


class PhoneNumberTests(SimpleTestCase):
    def test_multiple_noop(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "telefoonnummer",
            "label": "Telefoonnummer",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "telefoonnummer",
            "label": "Telefoonnummer",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "telefoonnummer",
            "label": "Telefoonnummer",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "telefoonnummer",
            "label": "Telefoonnummer",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "telefoonnummer",
            "label": "Telefoonnummer",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "telefoonnummer",
            "label": "Telefoonnummer",
            "defaultValue": ["0612345678", None, "0687654321"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["0612345678", "", "0687654321"])


class TextareaTests(SimpleTestCase):
    def test_multiple_noop(self):
        component: Component = {
            "type": "textarea",
            "key": "textArea",
            "label": "Textarea",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "textarea",
            "key": "textArea",
            "label": "Textarea",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "textarea",
            "key": "textArea",
            "label": "Textarea",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "textarea",
            "key": "textArea",
            "label": "Textarea",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "type": "textarea",
            "key": "textArea",
            "label": "Textarea",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "textarea",
            "key": "textArea",
            "label": "Textarea",
            "defaultValue": ["foo", None, "bar"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["foo", "", "bar"])


class IBANTests(SimpleTestCase):
    def test_multiple_noop(self):
        component: Component = {
            "type": "iban",
            "key": "iban",
            "label": "iban",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_noop(self):
        component: Component = {
            "type": "iban",
            "key": "iban",
            "label": "iban",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_default_value_none_changed(self):
        component: Component = {
            "type": "iban",
            "key": "iban",
            "label": "iban",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "iban",
            "key": "iban",
            "label": "iban",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_multiple_default_value_none_changed(self):
        component: Component = {
            "type": "iban",
            "key": "iban",
            "label": "iban",
            "defaultValue": [None],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [""])

    def test_multiple_default_value_with_none_changed(self):
        component: Component = {
            "type": "iban",
            "key": "iban",
            "label": "iban",
            "defaultValue": ["foo", None, "bar"],
            "multiple": True,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], ["foo", "", "bar"])


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


class MapTests(SimpleTestCase):
    def test_existing_interactions(self):
        component: MapComponent = {
            "key": "map",
            "type": "map",
            "label": "Map",
            "useConfigDefaultMapSettings": True,
            "interactions": {"marker": False, "polygon": True, "polyline": True},
        }

        changed = ensure_map_has_interactions(component)

        self.assertFalse(changed)

    def test_missing_interactions(self):
        component: MapComponent = {
            "key": "map",
            "type": "map",
            "label": "Map",
            "useConfigDefaultMapSettings": True,
        }

        changed = ensure_map_has_interactions(component)

        self.assertTrue(changed)
        self.assertEqual(
            component["interactions"],
            {"marker": True, "polygon": False, "polyline": False},
        )


class RadioTests(SimpleTestCase):
    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "radio",
            "key": "radio",
            "label": "Radio field",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_none_as_default_value_does_change(self):
        component: Component = {
            "type": "radio",
            "key": "radio",
            "label": "Radio field",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_empty_string_as_default_value_doesnt_change(self):
        component: Component = {
            "type": "radio",
            "key": "radio",
            "label": "Radio field",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)


class FileTests(SimpleTestCase):
    def test_none_as_default_value_does_change(self):
        component: Component = {
            "type": "file",
            "key": "file",
            "label": "File",
            "defaultValue": None,
        }

        changed = fix_file_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])

    def test_multiple_none_as_default_value_does_change(self):
        component: Component = {
            "type": "file",
            "key": "file",
            "label": "File",
            "multiple": True,
            "defaultValue": None,
        }

        changed = fix_file_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])

    def test_empty_list_as_default_value_doesnt_change(self):
        component: Component = {
            "type": "file",
            "key": "file",
            "label": "File",
            "defaultValue": [],
        }

        changed = fix_file_default_value(component)

        self.assertFalse(changed)

    def test_multiple_empty_list_as_default_value_doesnt_change(self):
        component: Component = {
            "type": "file",
            "key": "file",
            "label": "File",
            "multiple": True,
            "defaultValue": [],
        }

        changed = fix_file_default_value(component)

        self.assertFalse(changed)

    def test_none_in_list_as_default_value_does_change(self):
        component: Component = {
            "type": "file",
            "key": "file",
            "label": "File",
            "multiple": True,
            "defaultValue": [None],
        }

        changed = fix_file_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])


class CheckboxTests(SimpleTestCase):
    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "checkbox",
            "key": "checkbox",
            "label": "Checkbox",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_none_as_default_value_does_change(self):
        component: Component = {
            "type": "checkbox",
            "key": "checkbox",
            "label": "Checkbox",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], False)

    def test_boolean_as_default_value_doesnt_change(self):
        component: Component = {
            "type": "checkbox",
            "key": "checkbox",
            "label": "Checkbox",
            "defaultValue": False,
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)


class SignatureTests(SimpleTestCase):
    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "signature",
            "key": "signature",
            "label": "Signature",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_none_as_default_value_does_change(self):
        component: Component = {
            "type": "signature",
            "key": "signature",
            "label": "Signature",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_empty_string_as_default_value_doesnt_change(self):
        component: Component = {
            "type": "signature",
            "key": "signature",
            "label": "Signature",
            "defaultValue": "",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)


class EditGridTests(SimpleTestCase):
    def test_no_default_value_doesnt_change(self):
        component: Component = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Edit grid",
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)

    def test_none_as_default_value_does_change(self):
        component: Component = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Edit grid",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])

    def test_empty_list_as_default_value_doesnt_change(self):
        component: Component = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Edit grid",
            "defaultValue": [],
        }

        changed = fix_empty_default_value(component)

        self.assertFalse(changed)


class BSNTests(SimpleTestCase):
    def test_null_default_value(self):
        component: Component = {
            "type": "bsn",
            "key": "bsn",
            "label": "BSN",
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], "")

    def test_null_default_value_multiple(self):
        component: Component = {
            "type": "bsn",
            "key": "bsn",
            "label": "BSN",
            "multiple": True,
            "defaultValue": None,
        }

        changed = fix_empty_default_value(component)

        self.assertTrue(changed)
        self.assertEqual(component["defaultValue"], [])
