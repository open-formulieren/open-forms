import string
from urllib.parse import quote_plus, urlsplit

from django.test import SimpleTestCase

from furl import furl
from hypothesis import assume, example, given, strategies as st
from hypothesis.provisional import domains, urls

from ..client import is_base_url

printable_text = st.text(string.printable)


class IsBaseUrlTests(SimpleTestCase):
    @given(domains())
    def test_domain_without_protocol(self, item: str):
        assume(not item.startswith("http://"))
        assume(not item.startswith("https://"))

        self.assertFalse(is_base_url(item))

    @given(st.text(string.printable))
    @example("/some/absolute/path")
    def test_random_text_without_protocol(self, item: str):
        assume(not item.startswith("http://"))
        assume(not item.startswith("https://"))

        try:
            is_base = is_base_url(item)
        except ValueError:
            # furl got something that it can't parse as a URL, and we do want to bubble
            # this error up to the caller
            pass
        else:
            self.assertFalse(is_base)

    @given(
        st.sampled_from(["https", "http", "ftp", "file"]),
        st.lists(printable_text.map(quote_plus)).map("/".join),
    )
    def test_protocol_but_no_netloc(self, protocol, path):
        url = f"{protocol}:///{path}"

        self.assertFalse(is_base_url(url))

    @given(urls())
    def test_rfc_3986_url(self, url):
        assert url.startswith("http://") or url.startswith("https://")
        bits = urlsplit(url)
        # not allowed for communication between hosts - it's a way to request a dynamically
        # allocated port number.
        assume(bits.port != 0)

        self.assertTrue(is_base_url(url))

    @given(
        st.sampled_from(["ftp", "file", "madeupthing"]),
        domains(),
        st.lists(printable_text.map(quote_plus)).map("/".join),
    )
    def test_non_http_protocol(self, protocol, domain, path):
        url = f"{protocol}://{domain}/{path}"

        # we don't really care about the actual protocol, you *could* install a requests
        # adapter for non-http(s)
        self.assertTrue(is_base_url(url))

    def test_handle_str_or_furl_instance(self):
        example = "https://example.com/foo"

        with self.subTest("raw string"):
            self.assertTrue(is_base_url(example))

        with self.subTest("furl instance string"):
            self.assertTrue(is_base_url(furl(example)))
