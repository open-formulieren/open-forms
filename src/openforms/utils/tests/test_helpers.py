from django.test import TestCase

from openforms.utils.helpers import get_flattened_components


class TestGetFlattenedComponents(TestCase):
    def test_get_flattened_components_returns_a_flat_list_of_components_from_a_list_with_nested_components(
        self,
    ):
        components = [
            {"key": "key", "type": "textfield"},
            {"key": "key2", "type": "textarea"},
            {"key": "key3", "type": "checkbox"},
            {
                "key": "key4",
                "type": "fieldset",
                "components": [{"key": "key5", "type": "textfield"}],
            },
        ]

        flattened_components = get_flattened_components(components)

        self.assertEqual(
            flattened_components,
            [
                {"key": "key", "type": "textfield"},
                {"key": "key2", "type": "textarea"},
                {"key": "key3", "type": "checkbox"},
                {
                    "key": "key4",
                    "type": "fieldset",
                    "components": [{"key": "key5", "type": "textfield"}],
                },
                {"key": "key5", "type": "textfield"},
            ],
        )
