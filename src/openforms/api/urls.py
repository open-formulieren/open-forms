from django.urls import path, include

from openforms.core.api.router import core_urls

app_name = "api"

urlpatterns = [
    path("", include(core_urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
