from django.urls import include, path, re_path
from django.views.generic import TemplateView

from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from openforms.core.api.viewsets import (
    FormDefinitionViewSet,
    FormStepViewSet,
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

# submissions API
router.register(r"submissions", SubmissionViewSet)
submissions_router = NestedSimpleRouter(router, r"submissions", lookup="submission")
submissions_router.register(
    r"steps", SubmissionStepViewSet, basename="submission-steps"
)


urlpatterns = [
    # re_path(
    #     r"v1(?P<format>\.json|\.yaml)",
    #     schema_view.without_ui(cache_timeout=0),
    #     name="schema-json",
    # ),
    path(
        "v1/docs/",
        TemplateView.as_view(template_name="api_docs.html"),
        name="api-docs",
    ),
    path("v1/api-auth", include("rest_framework.urls", namespace="rest_framework")),
    path("v1/", include(router.urls)),
    path("v1/", include(forms_router.urls)),
    path("v1/", include(submissions_router.urls)),
]
