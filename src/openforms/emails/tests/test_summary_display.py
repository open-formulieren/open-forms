from django.template import Context, Template
from django.test import SimpleTestCase


class SummaryDisplayTest(SimpleTestCase):
    def test_display_value_template_tag(self):
        """
        part of a regression test for #990

        note this verifies the current situation, which notably does not localise
        """
        tests = [
            # single values
            (None, "None"),
            ("", ""),
            ("abc", "abc"),
            (123, "123"),
            # (123.45, "123,45"),  # localized
            # (10000, "10.000"),  # localized
            # (1000000.12, "1.000.000,12"),  # localized
            (123.45, "123.45"),  # not localized
            (10000, "10000"),  # not localized
            (1000000.12, "1000000.12"),  # not localized
            # lists
            ([], ""),
            ([None], "None"),
            ([None, None], "None, None"),
            ([1, 2, 3], "1, 2, 3"),
            # ([1.2, 123.45, 3.14, 1000000.12], f"1,2, 123,45, 3,14, 1000000.12"),# localized
            (
                [1.2, 123.45, 3.14, 1000000.12],
                f"1.2, 123.45, 3.14, 1000000.12",
            ),  # not localized
            (["", "", ""], ", , "),
            (["a", "b", "c"], "a, b, c"),
            ([["a", "b"], "c"], "a, b, c"),
            (
                [{"originalName": "foo.txt"}, {"originalName": "bar.txt"}],
                "foo.txt, bar.txt",
            ),
        ]
        template = Template("{% display_value value %}")
        for value, expected in tests:
            with self.subTest(f"{value}"):
                # actual = display_value(value)
                # instead render like the tag would
                actual = template.render(Context({"value": value}))
                self.assertEqual(actual, expected)
