from django.test import SimpleTestCase

from ..templatetags.style_dictionary import style_dictionary


class StyleDictionaryTests(SimpleTestCase):
    def test_simple(self):
        style_dict = {
            "foo": {"value": "bar"},
        }

        tokens = style_dictionary(style_dict, prefix="test")

        expected = {
            "--test-foo": "bar",
        }
        self.assertEqual(tokens, expected)

    def test_multiple_entries(self):
        style_dict = {
            "foo": {"value": "bar"},
            "baz": {"value": "quux"},
        }

        tokens = style_dictionary(style_dict, prefix="test")

        expected = {
            "--test-foo": "bar",
            "--test-baz": "quux",
        }
        self.assertEqual(tokens, expected)

    def test_different_nesting_levels(self):
        style_dict = {
            "foo": {"value": "bar"},
            "baz": {"quux": {"value": "nested"}},
        }

        tokens = style_dictionary(style_dict, prefix="test")

        expected = {
            "--test-foo": "bar",
            "--test-baz-quux": "nested",
        }
        self.assertEqual(tokens, expected)

    def test_documented_but_unexpected_nesting(self):
        """
        Edge case - the transformer should stop as soon as 'value' is detected.
        """
        style_dict = {"some": {"value": "foo", "token": {"value": "bar"}}}

        tokens = style_dictionary(style_dict, prefix="test")

        expected = {
            "--test-some": "foo",
        }
        self.assertEqual(tokens, expected)

    def test_prefix(self):
        style_dict = {"foo": {"value": "bar"}}

        tokens = style_dictionary(style_dict, prefix="of")

        self.assertEqual(tokens, {"--of-foo": "bar"})
