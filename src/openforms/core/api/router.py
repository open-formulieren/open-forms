from django.urls import path
from rest_framework import routers

from openforms.core.api.viewsets import ConfigurationView, FormViewSet


core_router = routers.DefaultRouter()

core_router.register(r"forms", FormViewSet)

core_urls = core_router.urls + [
    path("configurations/<str:slug>/", ConfigurationView.as_view(), name="configurations"),
]
