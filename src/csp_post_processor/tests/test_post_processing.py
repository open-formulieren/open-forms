import itertools
import re
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from csp_post_processor import post_process_html


def get_counter_side_effect(start=1):
    c = itertools.count(start=start)
    return lambda n: next(c)


class PostProcessingTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        factory = RequestFactory()
        self.factory = factory
        self.request = factory.get("/irrelevant", HTTP_X_CSP_NONCE="dGVzdA==")

    @patch("csp_post_processor.processor.get_html_id", return_value="1234")
    def test_move_inline_styles_to_nonced_style_tag(self, mock_get_html_id):
        html = """
        <div>
            <p>Some unstyled content</p>
            <p>Some <strong><span style="font-size: 12px">styled</span></strong> content.</p>
        </div>
        """

        converted = post_process_html(html, self.request)

        expected = """
        <style nonce="dGVzdA==">
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-1234 {
                font-size: 12px;
            }
        </style>
        <div>
            <p>Some unstyled content</p>
            <p>Some <strong><span id="nonce-5fa62ae6176f3746142503a6ebe96cb3-1234">styled</span></strong> content.</p>
        </div>
        """
        self.assertHTMLEqual(converted, expected)

    def test_reuse_existing_html_id_if_present(self):
        html = """
        <div>
            <p>Some unstyled content</p>
            <p>Some <strong><span id="predefined-id" style="font-size: 12px">styled</span></strong> content.</p>
        </div>
        """

        converted = post_process_html(html, self.request)

        expected = """
        <style nonce="dGVzdA==">
            #predefined-id {
                font-size: 12px;
            }
        </style>
        <div>
            <p>Some unstyled content</p>
            <p>Some <strong><span id="predefined-id">styled</span></strong> content.</p>
        </div>
        """
        self.assertHTMLEqual(converted, expected)

    def test_processing_without_nonce_in_request(self):
        requests = [
            self.factory.get("/irrelevant", HTTP_X_CSP_NONCE=""),
            self.factory.get("/irrelevant"),
        ]
        html = '<span style="color: red;">yep</span>'

        for request in requests:
            with self.subTest(headers=request.headers):
                result = post_process_html(html, request)

                # check that the markup is not modified
                self.assertHTMLEqual(result, html)

    def test_no_style_tag_emitted_without_styled_content(self):
        html = """
        <div>
            <p>Some unstyled content</p>
            <p>Some <strong>other</strong> content.</p>
        </div>
        """

        converted = post_process_html(html, self.request)

        expected = """
        <div>
            <p>Some unstyled content</p>
            <p>Some <strong>other</strong> content.</p>
        </div>
        """
        self.assertHTMLEqual(converted, expected)

    def test_invalid_html(self):
        invalid_html = "just plain text"

        converted = post_process_html(invalid_html, self.request)

        self.assertEqual(converted, "just plain text")

    @patch("csp_post_processor.processor.get_html_id")
    def test_processing_cleans_and_extracts_styles(self, mock_get_html_id):
        mock_get_html_id.side_effect = get_counter_side_effect()

        html = """
        <div style="width: 10px; background-image: url('://evil');">text</div>
        <span style="color: red;">text</span>
        <figure style="width: 5%;"><figcaption>text</figcaption></figure>
        """

        expected = """
        <style nonce="dGVzdA==">
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-1 {
                width: 10px;
            }
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-2 {
                color: red;
            }
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-3 {
                width: 5%;
            }
        </style>
        <div id="nonce-5fa62ae6176f3746142503a6ebe96cb3-1">text</div>
        <span id="nonce-5fa62ae6176f3746142503a6ebe96cb3-2">text</span>
        <figure id="nonce-5fa62ae6176f3746142503a6ebe96cb3-3"><figcaption>text</figcaption></figure>
        """

        converted = post_process_html(html, self.request)
        self.assertHTMLEqual(converted, expected)

    def test_processing_cleans_links(self):
        html = """
        <a href="http://example.com" target="_blank" rel="nofollow" title="text">text</a>
        <a href="https://example.com">text</a>
        <a href="evil://example.com">text</a>
        <a onclick="evil();">text</a>
        """

        expected = """
        <a href="http://example.com" target="_blank" rel="nofollow" title="text">text</a>
        <a href="https://example.com">text</a>
        <a>text</a>
        <a>text</a>
        """

        converted = post_process_html(html, self.request)
        self.assertHTMLEqual(converted, expected)

    def test_processing_cleans_images(self):
        html = """
        <img src="http://example.com" alt="text">
        <img src="data://xyz">
        <img src="evil://xyz" border="20">
        """

        expected = """
        <img src="http://example.com" alt="text">
        <img src="data://xyz">
        <img>
        """

        converted = post_process_html(html, self.request)
        self.assertHTMLEqual(converted, expected)

    def test_processing_cleans_scripts(self):
        html = """
        <script>evil();</script>
        <script src="https://example/code.js"></script>
        <script style="width:10px;">evil(); <b>text</b></script>
        """

        expected = ""

        converted = post_process_html(html, self.request)
        self.assertHTMLEqual(converted, expected)

    def test_processing_cleans_table(self):
        with self.subTest("simple"):
            html = """
            <table><tbody><tr><td>cell</td></tr></tbody></table>
            """

            expected = """
            <table><tbody><tr><td>cell</td></tr></tbody></table>
            """

            converted = post_process_html(html, self.request)
            self.assertHTMLEqual(converted, expected)

        with self.subTest("attrs"):
            html = """
            <table cellspacing="1"><tbody><tr><td colspan="2" rowspan="2">cell</td></tr></tbody></table>
            """

            expected = """
            <table><tbody><tr><td colspan="2" rowspan="2">cell</td></tr></tbody></table>
            """

            converted = post_process_html(html, self.request)
            self.assertHTMLEqual(converted, expected)

        with self.subTest("header"):
            html = """
            <table><thead><tr><th>cell</th></tr></thead><tbody><tr><td>cell</td></tr></tbody></table>
            """

            expected = """
            <table><thead><tr><th>cell</th></tr></thead><tbody><tr><td>cell</td></tr></tbody></table>
            """

            converted = post_process_html(html, self.request)
            self.assertHTMLEqual(converted, expected)

    def test_generated_html_ids_are_unique(self):
        # Regression test for #6917: the generated IDs were based on ``id(node)``,
        # which CPython reuses for the next element because lxml frees the element
        # proxies while iterating. Elements ended up sharing an ID and therefore got
        # each other's styles.
        html = "".join(
            f'<p style="text-align: center;">centered {i}</p>'
            "<div><p>unstyled</p>"
            f'<span style="background-color: yellow;">highlighted {i}</span></div>'
            for i in range(20)
        )

        converted = post_process_html(html, self.request)

        html_ids = re.findall(r'\bid="([^"]+)"', converted)
        self.assertEqual(len(html_ids), 40)
        self.assertEqual(len(set(html_ids)), 40)
        for html_id in html_ids:
            with self.subTest(html_id=html_id):
                self.assertIn(f"#{html_id} {{", converted)

    @patch("csp_post_processor.processor.get_html_id")
    def test_styles_on_inline_formatting_elements_are_kept(self, mock_get_html_id):
        # Regression test for #6917: the sanitizer stripped the generated ID from
        # bold/italic elements, so their styles were dropped.
        mock_get_html_id.side_effect = get_counter_side_effect()

        html = """
        <p>
            <strong style="background-color: yellow;">strong</strong>
            <em style="color: red;">em</em>
            <b style="color: green;">b</b>
            <i style="color: blue;">i</i>
        </p>
        """

        expected = """
        <style nonce="dGVzdA==">
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-1 {
                background-color: yellow;
            }
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-2 {
                color: red;
            }
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-3 {
                color: green;
            }
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-4 {
                color: blue;
            }
        </style>
        <p>
            <strong id="nonce-5fa62ae6176f3746142503a6ebe96cb3-1">strong</strong>
            <em id="nonce-5fa62ae6176f3746142503a6ebe96cb3-2">em</em>
            <b id="nonce-5fa62ae6176f3746142503a6ebe96cb3-3">b</b>
            <i id="nonce-5fa62ae6176f3746142503a6ebe96cb3-4">i</i>
        </p>
        """

        converted = post_process_html(html, self.request)
        self.assertHTMLEqual(converted, expected)
