"""Tests for AutoSchema Location header detection on create operations."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.urls import path

from drf_spectacular.generators import SchemaGenerator
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.schema import AutoSchema


def generate_schema(urlpatterns):
    generator = SchemaGenerator(patterns=urlpatterns)
    return generator.get_schema(request=None, public=True)


class WithUrlSerializer(serializers.Serializer):
    url = serializers.URLField()
    name = serializers.CharField()


class WithoutUrlSerializer(serializers.Serializer):
    name = serializers.CharField()


class DummyCreateView(CreateAPIView):
    serializer_class = WithUrlSerializer
    schema = AutoSchema()


class DummyPlainView(APIView):
    schema = AutoSchema()

    def post(self, request):
        return Response({"url": "", "name": ""}, status=201)


class SerializerHasUrlFieldTests(SimpleTestCase):
    """Unit tests for AutoSchema.serializer_has_url_field."""

    def check_schema_has_url_field(self, serializer) -> bool:
        schema = AutoSchema()
        schema.view = MagicMock()
        schema.method = "POST"
        with patch.object(schema, "get_response_serializers", return_value=serializer):
            return schema.serializer_has_url_field()

    def test_serializer_with_url_field(self):
        self.assertTrue(self.check_schema_has_url_field(WithUrlSerializer()))

    def test_serializer_without_url_field(self):
        self.assertFalse(self.check_schema_has_url_field(WithoutUrlSerializer()))

    def test_list_serializer_is_excluded(self):
        # ListSerializer wraps a child — should return False even if child has url
        list_ser = serializers.ListSerializer(child=WithUrlSerializer())
        self.assertFalse(self.check_schema_has_url_field(list_ser))

    def test_base_serializer_is_excluded(self):
        # BaseSerializer has no .fields — should return False
        base_ser = serializers.BaseSerializer()
        self.assertFalse(self.check_schema_has_url_field(base_ser))

    def test_serializer_class_accepted(self):
        # force_instance should instantiate the class; class with url → True
        self.assertTrue(self.check_schema_has_url_field(WithUrlSerializer))

    def test_none_response_serializer(self):
        # Some views return no serializer
        self.assertFalse(self.check_schema_has_url_field(None))


class LocationHeaderSchemaIntegrationTests(SimpleTestCase):
    """Verify Location header targets CreateModelMixin, not plain APIViews."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        urlpatterns = [
            path("create/", DummyCreateView.as_view(), name="dummy-create"),
            path("plain/", DummyPlainView.as_view(), name="dummy-plain"),
        ]
        cls.schema = generate_schema(urlpatterns)

    def test_create_view_has_location_header(self):
        create_op = self.schema["paths"]["/create/"]["post"]
        self.assertIn("Location", create_op["responses"]["201"].get("headers", {}))

    def test_plain_view_has_no_location_header(self):
        plain_op = self.schema["paths"]["/plain/"]["post"]
        for code, resp in plain_op["responses"].items():
            self.assertNotIn(
                "Location",
                resp.get("headers", {}),
                f"POST {code} on plain APIView should not have Location header",
            )
