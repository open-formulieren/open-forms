from django.test import SimpleTestCase

from ..printable import filter_printable


class PrintableUtilsTest(SimpleTestCase):
    def test_filter_printable(self):
        components = [
            # some printable
            {"type": "text"},
            {"type": "email"},
            {"type": "signature"},
            {"type": "unknown component"},
            # not printable
            {"type": "button"},
            {"type": "htmlelement"},
            {"type": "content"},
            {"type": "columns"},
            {"type": "fieldset"},
            {"type": "panel"},
            {"type": "tabs"},
            {"type": "well"},
            # cruft
            {"not_type": "not a valid component"},
        ]

        actual = list(filter_printable(components))
        expected = [
            {"type": "text"},
            {"type": "email"},
            {"type": "signature"},
            {"type": "unknown component"},
        ]
        self.assertEqual(actual, expected)
