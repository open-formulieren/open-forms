from django.test import SimpleTestCase

from hypothesis import given, strategies as st

from ..xml import INVALID_XML_CHARS


class XMLSanitizerTests(SimpleTestCase):
    @given(st.characters(min_codepoint=0x20, max_codepoint=0xD7FF))
    def test_valid_xml_characters(self, character):
        self.assertIsNone(INVALID_XML_CHARS.search(character))

    @given(st.characters(min_codepoint=0x00, max_codepoint=0x08))
    def test_invalid_xml_characters(self, character):
        self.assertIsNotNone(INVALID_XML_CHARS.search(character))
