from unittest import TestCase

from ..utils import flatten_by_path


class FlattenByPathTests(TestCase):
    def test_flat_input(self):
        configuration = {
            "components": [
                {
                    "key": "component1",
                    "type": "textfield",
                },
                {
                    "key": "component2",
                    "type": "textfield",
                },
            ]
        }

        result = flatten_by_path(configuration)

        self.assertEqual(
            result,
            {
                "components.0": configuration["components"][0],
                "components.1": configuration["components"][1],
            },
        )

    def test_nested_fieldset_and_columns(self):
        configuration = {
            "components": [
                {
                    "key": "component1",
                    "type": "textfield",
                },
                {
                    "key": "fieldset1",
                    "type": "fieldset",
                    "components": [
                        {
                            "key": "component3",
                            "type": "textfield",
                        },
                        {
                            "key": "component4",
                            "type": "textfield",
                        },
                    ],
                },
                {
                    "key": "columns1",
                    "type": "columns",
                    "columns": [
                        {"components": [{"type": "textfield", "key": "col1"}]},
                        {"components": [{"type": "textfield", "key": "col2"}]},
                    ],
                },
            ]
        }

        result = flatten_by_path(configuration)

        self.assertEqual(
            result,
            {
                "components.0": configuration["components"][0],
                "components.1": configuration["components"][1],
                "components.1.components.0": configuration["components"][1][
                    "components"
                ][0],
                "components.1.components.1": configuration["components"][1][
                    "components"
                ][1],
                "components.2": configuration["components"][2],
                "components.2.columns.0.components.0": configuration["components"][2][
                    "columns"
                ][0]["components"][0],
                "components.2.columns.1.components.0": configuration["components"][2][
                    "columns"
                ][1]["components"][0],
            },
        )
