from django.urls import path, include

from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from openforms.core.api.viewsets import (
    FormViewSet, FormDefinitionViewSet, FormStepViewSet
)
from openforms.submissions.api.viewsets import SubmissionViewSet, SubmissionStepViewSet

app_name = "api"

router = routers.DefaultRouter()
router.register(r'form-definitions', FormDefinitionViewSet)

router.register(r'forms', FormViewSet)
forms_router = NestedSimpleRouter(router, r'forms', lookup='form')
forms_router.register(r'steps', FormStepViewSet, basename='form-steps')

router.register(r'submissions', SubmissionViewSet)
submissions_router = NestedSimpleRouter(router, r'submissions', lookup='submission')
submissions_router.register(r'steps', SubmissionStepViewSet, basename='submission-steps')


urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("", include(router.urls)),
    path("", include(forms_router.urls)),
    path("", include(submissions_router.urls)),
]
