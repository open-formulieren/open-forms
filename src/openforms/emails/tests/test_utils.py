from django.test import SimpleTestCase

from ..utils import strip_tags_plus


class StripTagsPlusTests(SimpleTestCase):
    def test_strip_tags_no_keep_leading_whitespace(self):
        markup = """
        <p>Some paragraph</p>



           <p>another paragraph</p>"""

        output = strip_tags_plus(markup)

        expected = "Some paragraph\n\nanother paragraph\n"
        self.assertEqual(output, expected)

    def test_strip_tags_keep_leading_whitespace(self):
        markup = """
Some plain text

with some
  nested <p>markup</p>"""

        output = strip_tags_plus(markup, keep_leading_whitespace=True)

        expected = """Some plain text

with some
  nested markup
"""
        self.assertEqual(output, expected)
