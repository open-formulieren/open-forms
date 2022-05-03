import re
from io import StringIO

from lxml import etree
from lxml.etree import XMLSyntaxError
from lxml.html.clean import Cleaner


class HTMLAssertMixin:
    """
    Mixin HTML-related assertions.
    """

    def assertTagWithTextIn(self, tag, text, document_str):
        """
        check for html tags and their content while ignoring tag attributes
        """
        if not re.search(rf"<{tag}(?: [^>]*)?>\s*{text}", document_str):
            self.fail(f"cannot find <{tag}..>{text} in: {document_str}")

    def assertNotTagWithTextIn(self, tag, text, document_str):
        """
        check for html tags and their content while ignoring tag attributes
        """
        if re.search(rf"<{tag}(?: [^>]*)?>\s*{text}", document_str):
            self.fail(f"unexpectedly found <{tag}..>{text} in: {document_str}")

    def assertHTMLValid(self, html_text):
        """
        check basic HTML syntax validity
        """
        parser = etree.HTMLParser(recover=False)
        try:
            etree.parse(StringIO(html_text), parser)
        except XMLSyntaxError as e:
            self.fail(f"invalid html: {e}")


def strip_all_attributes(document: str) -> str:
    """
    Reduce an HTML document to just the tags, stripping any attributes.

    Useful for testing with self.assertInHTML without having to worry about class
    names, style tags etc.

    Taken and adapted from https://stackoverflow.com/a/7472003
    """
    cleaner = Cleaner(safe_attrs_only=True, safe_attrs=frozenset())
    cleansed = cleaner.clean_html(document)
    return cleansed
