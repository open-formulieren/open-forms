from django.test import SimpleTestCase

from openforms.utils.tests.html_assert import HTMLAssertMixin


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

    def test_assertHTMLValid(self):
        self.assertHTMLValid("<p></p>")

        with self.assertRaisesRegex(
            AssertionError, r"^invalid html: Unexpected end tag : p"
        ):
            self.assertHTMLValid("</p>")
