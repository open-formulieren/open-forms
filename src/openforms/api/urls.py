from django.urls import include, path
from django.views.generic import RedirectView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularRedocView,
)
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from openforms.forms.api.viewsets import (
    FormDefinitionViewSet,
    FormsImportAPIView,
    FormStepViewSet,
    FormVersionViewSet,
    FormViewSet,
)
from openforms.submissions.api.viewsets import SubmissionStepViewSet, SubmissionViewSet

# from .schema import schema_view

app_name = "api"

router = routers.DefaultRouter(trailing_slash=False)
# form definitions, raw Formio output
router.register(r"form-definitions", FormDefinitionViewSet)

# forms & their steps
router.register(r"forms", FormViewSet)
forms_router = NestedSimpleRouter(router, r"forms", lookup="form")
forms_router.register(r"steps", FormStepViewSet, basename="form-steps")
forms_router.register(r"versions", FormVersionViewSet, basename="form-versions")

# submissions API
router.register(r"submissions", SubmissionViewSet)
submissions_router = NestedSimpleRouter(router, r"submissions", lookup="submission")
submissions_router.register(
    r"steps", SubmissionStepViewSet, basename="submission-steps"
)

urlpatterns = [
    path("docs/", RedirectView.as_view(pattern_name="api:api-docs")),
    path(
        "v1/",
        include(
            [
                # API documentation
                path(
                    "",
                    SpectacularJSONAPIView.as_view(schema=None),
                    name="api-schema-json",
                ),
                path(
                    "docs/",
                    SpectacularRedocView.as_view(url_name="api:api-schema-json"),
                    name="api-docs",
                ),
                path("schema", SpectacularAPIView.as_view(schema=None), name="schema"),
                # actual API endpoints
                path(
                    "api-auth",
                    include("rest_framework.urls", namespace="rest_framework"),
                ),
                path("submissions/", include("openforms.submissions.api.urls")),
                path("forms-import", FormsImportAPIView.as_view(), name="forms-import"),
                path("prefill/", include("openforms.prefill.api.urls")),
                path("validation/", include("openforms.validations.api.urls")),
                path("location/", include("openforms.locations.api.urls")),
                path("authentication/", include("openforms.authentication.api.urls")),
                path("registration/", include("openforms.registrations.api.urls")),
                path("payment/", include("openforms.payments.api.urls")),
                path("", include(router.urls)),
                path("", include(forms_router.urls)),
                path("", include(submissions_router.urls)),
            ]
        ),
    ),
]
