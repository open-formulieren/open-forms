from rest_framework import serializers
from rest_framework.test import APIRequestFactory, APISimpleTestCase

from csp_post_processor.drf.fields import CSPPostProcessedHTMLField

from .mixins import InlineStylesMixin

TEST_HTML = """
<p>Part without inline styles</p>
<p>Some <span style="font-weight: 700;">inline styled</span> markup.</sp>
"""
data = {"html": TEST_HTML}


class TestSerializer(serializers.Serializer):
    html = CSPPostProcessedHTMLField()


class SerializerFieldTests(InlineStylesMixin, APISimpleTestCase):
    def setUp(self):
        super().setUp()

        factory = APIRequestFactory()
        self.factory = factory
        self.request = factory.get("/irrelevant", HTTP_X_CSP_NONCE="dGVzdA==")

    def test_missing_request_in_context(self):
        serializer = TestSerializer(instance=data, context={})

        post_processed = serializer.data["html"]

        self.assertEqual(post_processed, TEST_HTML)

    def test_post_processed_with_request_in_context(self):
        serializer = TestSerializer(instance=data, context={"request": self.request})

        post_processed = serializer.data["html"]

        style, content = self._parse_html(post_processed)
        self.assertEqual(len(content), 2)
        self.assertStyleNonce(style, "dGVzdA==")
        self.assertNoInlineStyles(content)
