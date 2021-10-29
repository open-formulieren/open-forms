import re

from django.test import SimpleTestCase


class HTMLAssertMixin:
    def assertTagWithTextIn(self, tag, text, document_str):
        """
        check for html tags and their content while ignoring tag attributes
        """
        if not re.search(f"<{tag}(?: [^>]*)?>\s*{text}", document_str):
            self.fail(f"cannot find <{tag}..>{text} in: {document_str}")

    def assertNotTagWithTextIn(self, tag, text, document_str):
        """
        check for html tags and their content while ignoring tag attributes
        """
        if re.search(f"<{tag}(?: [^>]*)?>\s*{text}", document_str):
            self.fail(f"unexpectedly found <{tag}..>{text} in: {document_str}")


class HTMLAssertMixinTest(HTMLAssertMixin, SimpleTestCase):
    def test_assertTagWithTextIn(self):
        html = """
        <td>aaa</td>
        <td style="foo:bar;">bbb</td>
        <td style="foo:bar;"><span>cccc</span></td>
        <p style="foo:bar;">
            xxx
        </p>
        """
        self.assertTagWithTextIn("td", "aaa", html)
        self.assertTagWithTextIn("td", "bbb", html)
        self.assertTagWithTextIn("span", "ccc", html)
        self.assertTagWithTextIn("p", "xxx", html)

        with self.assertRaisesRegex(AssertionError, r"^cannot find <td..>xyz in: "):
            self.assertTagWithTextIn("td", "xyz", html)

        with self.assertRaisesRegex(AssertionError, r"^cannot find <td..>ccc in: "):
            self.assertTagWithTextIn("td", "ccc", html)

        with self.assertRaisesRegex(AssertionError, r"^cannot find <x..>y in: "):
            self.assertTagWithTextIn("x", "y", html)

    def test_assertNotTagWithText(self):
        html = """
        <td>aaa</td>
        <td style="foo:bar;">bbb</td>
        <td style="foo:bar;"><span>cccc</span></td>
        """
        self.assertNotTagWithTextIn("td", "zzz", html)

        with self.assertRaisesRegex(
            AssertionError, r"^unexpectedly found <td..>aaa in: "
        ):
            self.assertNotTagWithTextIn("td", "aaa", html)
