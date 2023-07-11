from django.test import TestCase

from ..helpers import truncate_str_if_needed


class TruncateStrTests(TestCase):
    def test_str_is_truncated_when_max_length_exceeded(self):
        original_str = "This is the initial text"
        added_str = "This is the initial text (added text)"
        max_chars = 30

        result = truncate_str_if_needed(original_str, added_str, max_chars)

        self.assertEqual(result, "This is the init\u2026 (added text)")

    def test_not_trucated_str_is_returned_when_max_length_not_exceeded(self):
        original_str = "This is the text"
        added_str = "This is the text (added text)"
        max_chars = 30

        result = truncate_str_if_needed(original_str, added_str, max_chars)

        self.assertEqual(result, "This is the text (added text)")
