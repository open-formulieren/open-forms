from django.test import SimpleTestCase

from ..service import get_component_empty_value
from ..typing import (
    AddressNLComponent,
    CustomerProfileComponent,
    MapComponent,
    SelectBoxesComponent,
)


class GetComponentEmptyValueTests(SimpleTestCase):
    def test_selectboxes_default_value(self):
        component: SelectBoxesComponent = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Select Boxes",
            "values": [
                {"label": "a", "value": "a"},
                {"label": "b", "value": "b"},
                {"label": "c", "value": "c"},
            ],
            "defaultValue": {"a": False, "b": False, "c": False},
        }

        empty_value = get_component_empty_value(component)
        self.assertEqual(empty_value, {"a": False, "b": False, "c": False})

    def test_selectboxes_configuration_updated_and_no_default_value(self):
        # This is the situation when the data source is another variable or reference
        # lists, AND the configuration was dynamically updated
        component: SelectBoxesComponent = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Select Boxes",
            "values": [
                {"label": "a", "value": "a"},
                {"label": "b", "value": "b"},
                {"label": "c", "value": "c"},
            ],
            "defaultValue": {},
        }

        empty_value = get_component_empty_value(component)
        self.assertEqual(empty_value, {"a": False, "b": False, "c": False})

    def test_selectboxes_configruation_not_updated_and_no_default_value(self):
        # If the configuration was not updated, the 'values' list has one entry with
        # the 'label' and 'value' an empty string.
        component: SelectBoxesComponent = {
            "key": "selectboxes",
            "type": "selectboxes",
            "label": "Select Boxes",
            "values": [
                {"label": "", "value": ""},
            ],
        }

        empty_value = get_component_empty_value(component)
        self.assertEqual(empty_value, {})

    def test_addressnl_empty_value(self):
        component: AddressNLComponent = {
            "key": "address",
            "type": "addressNL",
            "label": "addressNL",
            "deriveAddress": False,
        }

        empty_value = get_component_empty_value(component)

        self.assertEqual(
            empty_value,
            {
                "postcode": "",
                "houseNumber": "",
                "houseLetter": "",
                "houseNumberAddition": "",
                "streetName": "",
                "city": "",
                "secretStreetCity": "",
                "autoPopulated": False,
            },
        )

    def test_map_empty_value(self):
        component: MapComponent = {
            "key": "map",
            "type": "map",
            "label": "map",
            "useConfigDefaultMapSettings": True,
            "interactions": {
                "marker": True,
                "polygon": False,
                "polyline": False,
            },
        }

        empty_value = get_component_empty_value(component)

        self.assertIsNone(empty_value)

    def test_customer_profile_empty_value(self):
        component: CustomerProfileComponent = {
            "key": "customerProfile",
            "type": "customerProfile",
            "label": "customerProfile",
            "shouldUpdateCustomerData": False,
            "digitalAddressTypes": ["email", "phoneNumber"],
        }

        empty_value = get_component_empty_value(component)

        self.assertEqual(
            empty_value,
            [
                {
                    "type": "email",
                    "address": "",
                    "preferenceUpdate": "useOnlyOnce",
                },
                {
                    "type": "phoneNumber",
                    "address": "",
                    "preferenceUpdate": "useOnlyOnce",
                },
            ],
        )
