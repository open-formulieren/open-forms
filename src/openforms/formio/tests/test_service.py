from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import reverse

from openforms.formio.service import (
    FormioConfigurationWrapper,
    rewrite_formio_components_for_request,
)


class ServiceTestCase(TestCase):
    @patch("csp_post_processor.processor.get_html_id", return_value="1234")
    def test_rewrite_formio_components_for_request(self, m):
        request = RequestFactory().get("/", HTTP_X_CSP_NONCE="dGVzdA==")

        configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e1a2cv9",
                    "key": "my_file",
                    "type": "file",
                    "url": "bad",
                },
                {
                    "id": "e2a2cv9",
                    "key": "my_content",
                    "type": "content",
                    "html": '<img style="width: 90%; border: 5000px solid red;">',
                },
            ],
        }
        rewrite_formio_components_for_request(
            FormioConfigurationWrapper(configuration), request
        )
        with self.subTest("temporary file upload url"):
            url = request.build_absolute_uri(
                reverse("api:formio:temporary-file-upload")
            )
            self.assertEqual(configuration["components"][0]["url"], url)

        with self.subTest("content html/css CSP"):
            # note the CSS declarations are filtered
            expected = """
            <style nonce="dGVzdA==">
            #nonce-5fa62ae6176f3746142503a6ebe96cb3-1234 {
                width: 90%;
            }
            </style>
            <img id="nonce-5fa62ae6176f3746142503a6ebe96cb3-1234">
            """
            self.assertHTMLEqual(configuration["components"][1]["html"], expected)
