from django.test import TestCase

from openforms.utils.context_processors import filesizeformat_integers


class ContextProcessorTests(TestCase):
    def test_integer_max_filesize(self):
        max_file_size = 52428800

        max_file_size_string = filesizeformat_integers(max_file_size)

        self.assertIn("50\xa0MB", max_file_size_string)
