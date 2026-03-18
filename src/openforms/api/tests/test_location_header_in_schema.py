"""Tests for AutoSchema Location header detection on create operations."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from drf_spectacular.generators import SchemaGenerator
from rest_framework import routers, serializers

from openforms.api.schema import AutoSchema


def generate_schema(route, viewset):
    router = routers.SimpleRouter()
    router.register(route, viewset, basename=route)
    generator = SchemaGenerator(patterns=router.urls)
    return generator.get_schema(request=None, public=True)


class _WithUrlSerializer(serializers.Serializer):
    url = serializers.URLField()
    name = serializers.CharField()


class _WithoutUrlSerializer(serializers.Serializer):
    name = serializers.CharField()


class SerializerHasUrlFieldTests(TestCase):
    """Unit tests for AutoSchema._serializer_has_url_field."""

    def _make_schema(self, serializer):
        schema = AutoSchema()
        schema.view = MagicMock()
        schema.method = "POST"
        with patch.object(schema, "get_response_serializers", return_value=serializer):
            return schema._serializer_has_url_field()

    def test_serializer_with_url_field(self):
        self.assertTrue(self._make_schema(_WithUrlSerializer()))

    def test_serializer_without_url_field(self):
        self.assertFalse(self._make_schema(_WithoutUrlSerializer()))

    def test_list_serializer_is_excluded(self):
        # ListSerializer wraps a child — should return False even if child has url
        list_ser = serializers.ListSerializer(child=_WithUrlSerializer())
        self.assertFalse(self._make_schema(list_ser))

    def test_base_serializer_is_excluded(self):
        # BaseSerializer has no .fields — should return False
        base_ser = serializers.BaseSerializer()
        self.assertFalse(self._make_schema(base_ser))

    def test_serializer_class_accepted(self):
        # force_instance should instantiate the class; class with url → True
        self.assertTrue(self._make_schema(_WithUrlSerializer))

    def test_none_response_serializer(self):
        # Some views return no serializer
        self.assertFalse(self._make_schema(None))


class GetOverrideParametersTests(TestCase):
    """Unit tests for the Location header injection in get_override_parameters."""

    def _get_location_param(self, is_create, has_url_field):
        schema = AutoSchema()
        schema.view = MagicMock()
        schema.method = "POST" if is_create else "GET"
        with (
            patch.object(
                schema, "_is_create_operation", return_value=is_create
            ),
            patch.object(
                schema, "_serializer_has_url_field", return_value=has_url_field
            ),
        ):
            params = schema.get_override_parameters()
        return [p for p in params if getattr(p, "name", None) == "Location"]

    def test_location_added_for_create_with_url_field(self):
        location_params = self._get_location_param(is_create=True, has_url_field=True)
        self.assertEqual(len(location_params), 1)

    def test_no_location_for_create_without_url_field(self):
        location_params = self._get_location_param(is_create=True, has_url_field=False)
        self.assertEqual(len(location_params), 0)

    def test_no_location_for_non_create_with_url_field(self):
        location_params = self._get_location_param(is_create=False, has_url_field=True)
        self.assertEqual(len(location_params), 0)


class LocationHeaderSchemaIntegrationTests(TestCase):
    """Verify Location header presence/absence using a schema built from FormDefinitionViewSet."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from openforms.forms.api.viewsets import FormDefinitionViewSet

        cls.schema = generate_schema("form-definitions", FormDefinitionViewSet)

    def test_location_header_only_on_create_responses(self):
        # POST (create) → Location in 201; GET/PUT/PATCH → absent
        paths = self.schema["paths"]
        list_create = paths["/form-definitions/"]
        detail = paths["/form-definitions/{uuid}/"]

        self.assertIn("Location", list_create["post"]["responses"]["201"].get("headers", {}))

        for method, responses in [
            ("get", list_create["get"]["responses"]),
            ("put", detail.get("put", {}).get("responses", {})),
            ("patch", detail.get("patch", {}).get("responses", {})),
        ]:
            for code, resp in responses.items():
                self.assertNotIn(
                    "Location",
                    resp.get("headers", {}),
                    f"{method.upper()} {code} should not have Location header",
                )
