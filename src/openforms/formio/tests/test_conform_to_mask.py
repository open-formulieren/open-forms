from django.test import SimpleTestCase

from ..utils import conform_to_mask


class ConformToMaskTests(SimpleTestCase):
    def test_valid_conversions(self):
        valid = (
            ("9999 AA", "1000AA", "1000 AA"),
            ("9999 AA", "1000 AA", "1000 AA"),
            ("9999 AA", "1000  AA", "1000 AA"),
            ("9999 AA", "1000 aA", "1000 aA"),
            ("9999AA", "1000AA", "1000AA"),
            ("9999AA", "1015 CJ", "1015CJ"),
            ("9999AA", "1015 cj", "1015cj"),
            ("9999AA", "1015 cJ", "1015cJ"),
            ("ab:a9", "Zb:Y3", "zb:y3"),
            ("(999) 999-99", "(123)456-78", "(123) 456-78"),
            ("(999) 999-99", "(123) 456-78", "(123) 456-78"),
            ("**-99", "E3-55", "E3-55"),
        )

        for mask, value, expected in valid:
            with self.subTest(mask=mask, input=value, expected=expected):
                result = conform_to_mask(value, mask)

                self.assertEqual(result, expected)

    def test_invalid_conversions(self):
        invalid = (
            ("9999 AA", "abc8 CJ"),
            ("9999 AA", "1234 30"),
            # TODO: we probably *could* convert non-input characters from the mask
            ("ab:a9", "Zb-Y3"),
            ("**-99", "^%-55"),
            ("9999 AA", "1000 A"),
            ("9999 AA", "1000A"),
        )

        for mask, value in invalid:
            with self.subTest(mask=mask, input=value):
                with self.assertRaises(ValueError):
                    conform_to_mask(value, mask)
