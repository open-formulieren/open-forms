from django.test import TestCase

from ..utils import html_escape_json


class EscapeHTMLTests(TestCase):
    def test_given_dicts_values_are_escaped(self):
        dict_sample = {
            "test1": "normal value",
            "test2": """<>'"&""",
            "nested_dict": {
                "nested_dict1": {"nested_dict2": {"escape": """<>'"&"""}},
            },
            "nested_list": [
                "escape < me",
                {"leave > me": "escape & me"},
            ],
        }

        expected_dict = {
            "test1": "normal value",
            "test2": "&lt;&gt;&#x27;&quot;&amp;",
            "nested_dict": {
                "nested_dict1": {
                    "nested_dict2": {"escape": "&lt;&gt;&#x27;&quot;&amp;"}
                },
            },
            "nested_list": [
                "escape &lt; me",
                {"leave > me": "escape &amp; me"},
            ],
        }

        dict_result = html_escape_json(dict_sample)

        self.assertEqual(expected_dict, dict_result)

    def test_given_lists_values_are_escaped(self):
        list_sample = [
            "test",
            """<>'"&""",
            "escape < me",
            ["escape < me"],
            [{"nested_dict": "escape < me"}],
        ]
        expected_list = [
            "test",
            "&lt;&gt;&#x27;&quot;&amp;",
            "escape &lt; me",
            ["escape &lt; me"],
            [{"nested_dict": "escape &lt; me"}],
        ]

        list_result = html_escape_json(list_sample)

        self.assertEqual(expected_list, list_result)

    def test_different_input(self):
        samples = [5, 5.9, None, True]

        for sample in samples:
            with self.subTest(sample=sample):
                result = html_escape_json(sample)

                self.assertIs(result, sample)
