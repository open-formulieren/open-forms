from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from hypothesis import given, settings

from ..typing import (
    ColumnsComponent,
    Component,
    ContentComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
)
from ..validators import variable_key_validator
from .search_strategies import (
    address_nl_component,
    any_component,
    bsn_component,
    checkbox_component,
    columns_component,
    content_component,
    cosign_v1_component,
    cosign_v2_component,
    currency_component,
    date_component,
    datetime_component,
    edit_grid_component,
    email_component,
    fieldset_component,
    file_component,
    formio_key,
    iban_component,
    license_plate_component,
    map_component,
    np_family_members_component,
    number_component,
    phone_number_component,
    postcode_component,
    radio_component,
    select_component,
    selectboxes_component,
    signature_component,
    textarea_component,
    textfield_component,
    time_component,
)


class SearchStrategyTests(SimpleTestCase):
    @given(formio_key())
    def test_formio_key_validates(self, key: str):
        self.assertNotIn("\n", key)
        try:
            variable_key_validator(key)
        except ValidationError:
            self.fail("Generated formio key did not pass validation")

    @given(any_component)
    def test_any_component(self, component: Component):
        self.assertIn("type", component)
        self.assertIn("key", component)

    @given(textfield_component())
    def test_textfield_component(self, component: Component):
        self.assertEqual(component["type"], "textfield")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(email_component())
    def test_email_component(self, component: Component):
        self.assertEqual(component["type"], "email")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(date_component())
    def test_date_component(self, component: Component):
        self.assertEqual(component["type"], "date")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(datetime_component())
    def test_datetime_component(self, component: Component):
        self.assertEqual(component["type"], "datetime")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(time_component())
    def test_time_component(self, component: Component):
        self.assertEqual(component["type"], "time")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(phone_number_component())
    def test_phone_number_component(self, component: Component):
        self.assertEqual(component["type"], "phoneNumber")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(file_component())
    def test_file_component(self, component: Component):
        self.assertEqual(component["type"], "file")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(textarea_component())
    def test_textarea_component(self, component: Component):
        self.assertEqual(component["type"], "textarea")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(number_component())
    def test_number_component(self, component: Component):
        self.assertEqual(component["type"], "number")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(select_component())
    def test_select_component(self, component: SelectComponent):
        self.assertEqual(component["type"], "select")
        self.assertIn("key", component)
        self.assertIn("label", component)

        assert "data" in component
        assert "values" in component["data"]
        for value in component["data"]["values"]:
            self.assertIn("value", value)
            self.assertIn("label", value)

    @given(checkbox_component())
    def test_checkbox_component(self, component: Component):
        self.assertEqual(component["type"], "checkbox")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(selectboxes_component())
    def test_selectboxes_component(self, component: SelectBoxesComponent):
        self.assertEqual(component["type"], "selectboxes")
        self.assertIn("key", component)
        self.assertIn("label", component)

        assert "values" in component
        for value in component["values"]:
            self.assertIn("value", value)
            self.assertIn("label", value)

    @given(currency_component())
    def test_currency_component(self, component: Component):
        self.assertEqual(component["type"], "currency")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(radio_component())
    def test_radio_component(self, component: RadioComponent):
        self.assertEqual(component["type"], "radio")
        self.assertIn("key", component)
        self.assertIn("label", component)

        assert "values" in component
        for value in component["values"]:
            self.assertIn("value", value)
            self.assertIn("label", value)

    @given(iban_component())
    def test_iban_component(self, component: Component):
        self.assertEqual(component["type"], "iban")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(license_plate_component())
    def test_license_plate_component(self, component: Component):
        self.assertEqual(component["type"], "licenseplate")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(bsn_component())
    def test_bsn_component(self, component: Component):
        self.assertEqual(component["type"], "bsn")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(address_nl_component())
    def test_address_nl_component(self, component: Component):
        self.assertEqual(component["type"], "addressNL")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(np_family_members_component())
    def test_np_family_members_component(self, component: Component):
        self.assertEqual(component["type"], "npFamilyMembers")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(signature_component())
    def test_signature_component(self, component: Component):
        self.assertEqual(component["type"], "signature")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(cosign_v2_component())
    def test_cosign_v2_component(self, component: Component):
        self.assertEqual(component["type"], "cosign")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(map_component())
    def test_map_component(self, component: Component):
        self.assertEqual(component["type"], "map")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(postcode_component())
    def test_postcode_component(self, component: Component):
        self.assertEqual(component["type"], "postcode")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(cosign_v1_component())
    def test_cosign_v1_component(self, component: Component):
        self.assertEqual(component["type"], "coSign")
        self.assertIn("key", component)
        self.assertIn("label", component)

    @given(content_component())
    def test_content_component(self, component: ContentComponent):
        self.assertEqual(component["type"], "content")
        self.assertIn("key", component)
        self.assertIn("label", component)
        self.assertIn("html", component)

    @given(edit_grid_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=10)
    def test_edit_grid_component(self, component: Component):
        self.assertEqual(component["type"], "editgrid")
        self.assertIn("key", component)
        self.assertIn("label", component)
        self.assertIn("components", component)

        for nested in component["components"]:
            self.assertIn("type", nested)

    @given(fieldset_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=10)
    def test_fieldset_component(self, component: Component):
        self.assertEqual(component["type"], "fieldset")
        self.assertIn("key", component)
        self.assertIn("label", component)

        self.assertIn("components", component)

        for nested in component["components"]:
            self.assertIn("type", nested)

    @given(columns_component())
    # recursive structure, more expensive to draw examples
    @settings(max_examples=10)
    def test_columns_component(self, component: ColumnsComponent):
        self.assertEqual(component["type"], "columns")
        self.assertIn("key", component)
        self.assertNotIn("label", component)

        self.assertIn("columns", component)

        for column in component["columns"]:
            self.assertIn("size", column)
            self.assertLessEqual(column["size"], 12)
            self.assertGreaterEqual(column["size"], 1)

            self.assertIn("components", column)

            for nested in column["components"]:
                self.assertIn("type", nested)
