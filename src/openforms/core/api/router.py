from django.urls import path

from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from openforms.core.api.viewsets import (
    FormViewSet, FormDefinitionViewSet, FormStepViewSet, FormSubmissionViewSet
)


core_router = routers.DefaultRouter()

core_router.register(r'form-definitions', FormDefinitionViewSet)

core_router.register(r'form-submissions', FormSubmissionViewSet)

core_router.register(r'forms', FormViewSet)

forms_router = NestedSimpleRouter(core_router, r'forms', lookup='form')

forms_router.register(r'steps', FormStepViewSet, basename='form-steps')

core_urls = core_router.urls + forms_router.urls
