from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularRedocView,
)
from rest_framework import routers

from openforms.forms.api.v3.viewsets import FormViewSet
from openforms.utils.decorators import never_cache
from openforms.utils.urls import decorator_include

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"forms", FormViewSet, basename="form")

app_name = "api"


urlpatterns = [
    # API documentation
    path(
        "v3/",
        include(
            [
                path(
                    "",
                    SpectacularJSONAPIView.as_view(schema=None),
                    name="api-schema-json",
                ),
                path(
                    "docs/",
                    SpectacularRedocView.as_view(url_name="api:v3:api-schema-json"),
                    name="api-docs",
                ),
                path("schema", SpectacularAPIView.as_view(schema=None), name="schema"),
            ]
        ),
    ),
    # actual API endpoints
    path(
        "v3/",
        decorator_include(
            never_cache,
            [
                path("", include(router.urls)),
            ],
        ),
    ),
]
