from django.urls import include, path

from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from openforms.core.api.viewsets import (
    FormDefinitionViewSet,
    FormStepViewSet,
    FormViewSet,
)
from openforms.submissions.api.viewsets import (
    FormSubmissionViewSet, SubmissionStepViewSet, SubmissionViewSet
)

app_name = "api"

router = routers.DefaultRouter(trailing_slash=False)
# form definitions, raw Formio output
router.register(r'form-definitions', FormDefinitionViewSet)

# forms & their steps
router.register(r'forms', FormViewSet)
forms_router = NestedSimpleRouter(router, r'forms', lookup='form')
forms_router.register(r'steps', FormStepViewSet, basename='form-steps')

# submissions API
router.register(r'submissions', SubmissionViewSet)
submissions_router = NestedSimpleRouter(router, r'submissions', lookup='submission')
submissions_router.register(r'steps', SubmissionStepViewSet, basename='submission-steps')

router.register(r'form-submissions', FormSubmissionViewSet, basename='form-submissions')


urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("", include(router.urls)),
    path("", include(forms_router.urls)),
    path("", include(submissions_router.urls)),
]
