from unittest.mock import patch

from django.contrib import admin
from django.test import override_settings
from django.urls import include, path

from drf_spectacular.views import SpectacularJSONAPIView
from rest_framework import serializers, status
from rest_framework.test import APITestCase
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from csp_post_processor.drf.fields import CSPPostProcessedHTMLField

from .models import Model


class IgnoredSerializer(serializers.Serializer):
    dummy = serializers.CharField()


class PostProcessSerializer(serializers.Serializer):
    wysiwyg = CSPPostProcessedHTMLField()


class ViewWithoutSerializer(APIView):
    def get(self, request):
        return None


class IgnoredView(APIView):
    serializer_class = IgnoredSerializer

    def get(self, request):
        return None


class PostProcessView(APIView):
    serializer_class = PostProcessSerializer

    def get(self, request):
        return None


class ViewSetWithoutSerializer(GenericViewSet):
    def list(self, request):
        return None


class ListSerializerViewSet(ModelViewSet):
    queryset = Model.objects.none()

    def get_serializer(self, *args, **kwargs):
        kwargs = {**kwargs, "many": True}
        return PostProcessSerializer(*args, **kwargs)


urlpatterns = [
    path(
        "",
        SpectacularJSONAPIView.as_view(schema=None),
        name="api-schema-json",
    ),
    path("endpoint1", ViewWithoutSerializer.as_view()),
    path("endpoint2", IgnoredView.as_view()),
    path("endpoint3", PostProcessView.as_view()),
    path("endpoint4", ViewSetWithoutSerializer.as_view({"get": "list"})),
    path("endpoint5", ListSerializerViewSet.as_view({"get": "list"})),
    # url resolver complains otherwise on other exceptions
    path("admin/", admin.site.urls),
    path("csp/", include("cspreports.urls")),
]


@override_settings(ROOT_URLCONF=__name__)
class SchemaGenerationExtensionTests(APITestCase):
    def test_expected_schema_generation(self):
        # can't use override_settings because drf-spectacular doesn't seem to
        # listen to settings_changed to clear internal caches
        with patch("drf_spectacular.drainage.GENERATOR_STATS.silent", new=True):
            response = self.client.get("")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = response.json()

        with self.subTest(endpoint="/endpoint1"):
            operation = schema["paths"]["/endpoint1"]["get"]

            self.assertNotIn("parameters", operation)  # no header expected

        with self.subTest(endpoint="/endpoint2"):
            operation = schema["paths"]["/endpoint2"]["get"]

            self.assertNotIn("parameters", operation)  # no header expected

        with self.subTest(endpoint="/endpoint3"):
            operation = schema["paths"]["/endpoint3"]["get"]

            self.assertIn("parameters", operation)  # header expected
            parameter = operation["parameters"][0]
            self.assertEqual(parameter["in"], "header")
            self.assertEqual(parameter["name"], "X-CSP-Nonce")

        with self.subTest(endpoint="/endpoint4"):
            operation = schema["paths"]["/endpoint4"]["get"]

            self.assertNotIn("parameters", operation)  # no header expected

        with self.subTest(endpoint="/endpoint5"):
            operation = schema["paths"]["/endpoint5"]["get"]

            self.assertIn("parameters", operation)  # header expected
            parameter = operation["parameters"][0]
            self.assertEqual(parameter["in"], "header")
            self.assertEqual(parameter["name"], "X-CSP-Nonce")
