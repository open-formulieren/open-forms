from django.test import TestCase

from ..utils import escape_html_manually


class EscapeHTMLTests(TestCase):
    def test_given_dict_values_are_escaped(self):
        sample = {
            "test1": "normal value",
            "test2": "<script>alert();</script>",
            "nested1": {
                "n_test": {"escape": "<script>alert();</script>"},
            },
        }
        expected = {
            "test1": "normal value",
            "test2": "&lt;script&gt;alert();&lt;/script&gt;",
            "nested1": {
                "n_test": {"escape": "&lt;script&gt;alert();&lt;/script&gt;"},
            },
        }

        result = escape_html_manually(sample)

        self.assertEqual(expected, result)

    def test_not_type_of_dict_returns_empty_dict(self):
        samples = [["test"], "test", 6]

        for sample in samples:
            with self.subTest(sample=sample):
                result = escape_html_manually(sample)

                self.assertEqual(result, {})
