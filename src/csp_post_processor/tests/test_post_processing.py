from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from csp_post_processor import post_process_html


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

    def test_invalid_html(self):
        invalid_html = "just plain text"

        converted = post_process_html(invalid_html, self.request)

        self.assertEqual(converted, "just plain text")
