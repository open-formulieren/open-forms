from io import BytesIO

from django.test import SimpleTestCase

from ..parsers import PlainTextParser


class PlainTextParserTestCase(SimpleTestCase):
    def test_simple(self):
        parser = PlainTextParser()

        parsed_result = parser.parse(BytesIO(b"foobar"))

        self.assertEqual(parsed_result, b"foobar")
