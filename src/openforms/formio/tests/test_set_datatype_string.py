from django.test import SimpleTestCase, tag

from openforms.formio.typing import SelectComponent

from ..migration_converters import set_datatype_string


class SetDatatypeStringTests(SimpleTestCase):
    @tag("gh-4772")
    def test_set_datatype_string(self):
        configuration: SelectComponent = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "data": {
                "values": [
                    {"label": "Option 1", "value": "1"},
                    {"label": "Option 2", "value": "2"},
                ]
            },
        }

        set_datatype_string(configuration)

        assert "dataType" in configuration
        self.assertEqual(configuration["dataType"], "string")

        configuration: SelectComponent = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "dataType": "integer",
            "data": {
                "values": [
                    {"label": "Option 1", "value": "1"},
                    {"label": "Option 2", "value": "2"},
                ]
            },
        }

        set_datatype_string(configuration)

        assert "dataType" in configuration
        self.assertEqual(configuration["dataType"], "string")

        configuration: SelectComponent = {
            "type": "select",
            "key": "select",
            "label": "Select",
            "dataType": "string",
            "data": {
                "values": [
                    {"label": "Option 1", "value": "1"},
                    {"label": "Option 2", "value": "2"},
                ]
            },
        }

        set_datatype_string(configuration)

        assert "dataType" in configuration
        self.assertEqual(configuration["dataType"], "string")
