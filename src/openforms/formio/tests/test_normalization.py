from django.test import SimpleTestCase, tag

from ..service import normalize_value_for_component
from ..typing import Component


class NormalizationTests(SimpleTestCase):
    def test_postcode_normalization_with_space(self):
        component = {
            "type": "postcode",
            "inputMask": "9999 AA",
        }
        values = ["1015CJ", "1015 CJ", "1015 cj", "1015cj"]

        for value in values:
            with self.subTest(value=value):
                result = normalize_value_for_component(component, value)

                self.assertEqual(result.upper(), "1015 CJ")

    def test_postcode_normalization_without_space(self):
        component = {
            "type": "postcode",
            "inputMask": "9999AA",
        }
        values = ["1015CJ", "1015 CJ", "1015 cj", "1015cj"]

        for value in values:
            with self.subTest(value=value):
                result = normalize_value_for_component(component, value)

                self.assertEqual(result.upper(), "1015CJ")

    def test_empty_value(self):
        component = {
            "type": "postcode",
            "inputMask": "9999AA",
        }

        result = normalize_value_for_component(component, "")

        self.assertEqual(result, "")

    def test_value_invalid_for_mask(self):
        component = {
            "type": "postcode",
            "inputMask": "9999AA",
        }

        result = normalize_value_for_component(component, "AAAA 34")

        self.assertEqual(result, "AAAA 34")

    def test_no_input_mask_given(self):
        component: Component = {
            "type": "postcode",
            "key": "dummy",
            "label": "Dummy",
        }

        result = normalize_value_for_component(component, "AAAA 34")

        self.assertEqual(result, "AAAA 34")

    def test_normalize_unknown_component_type(self):
        component: Component = {
            "type": "7923abf1-1397-40ed-b194-7a1d05e23b23",
            "key": "dummy",
            "label": "Dummy",
        }

        result = normalize_value_for_component(component, "foo.bar-baz")

        self.assertEqual(result, "foo.bar-baz")  # unmodified

    @tag("gh-4774")
    def test_textfield_normalization_non_str(self):
        component: Component = {
            "type": "textfield",
            "key": "dummy",
            "label": "Dummy",
        }

        int_result = normalize_value_for_component(component, 9)
        float_result = normalize_value_for_component(component, 9.9)

        self.assertEqual(int_result, "9")
        self.assertEqual(float_result, "9.9")
