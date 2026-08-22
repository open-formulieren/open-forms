from unittest.mock import patch

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from formio_types import Content

from ..service import (
    FormioConfig,
    rewrite_formio_components_for_request,
)
from ..typing import ContentComponent


class ServiceTestCase(TestCase):
    @patch("csp_post_processor.processor.get_html_id", return_value="1234")
    def test_rewrite_formio_components_for_request(self, m):
        request = APIRequestFactory().get("/", HTTP_X_CSP_NONCE="dGVzdA==")
        component: ContentComponent = {
            "id": "e2a2cv9",
            "key": "my_content",
            "label": "my_content",
            "type": "content",
            "html": '<img style="width: 90%; border: 5000px solid red;">',
        }
        config = FormioConfig(name="<test>", components=[component])

        rewrite_formio_components_for_request(config, request)

        content = config["my_content"]
        assert isinstance(content, Content)

        # note the CSS declarations are filtered
        expected = """
        <style nonce="dGVzdA==">
        #nonce-5fa62ae6176f3746142503a6ebe96cb3-1234 {
            width: 90%;
        }
        </style>
        <img id="nonce-5fa62ae6176f3746142503a6ebe96cb3-1234">
        """
        self.assertHTMLEqual(content.html, expected)
