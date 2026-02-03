from django.urls import include, path
from django.views.generic import RedirectView

app_name = "api"

urlpatterns = [
    path("docs/", RedirectView.as_view(pattern_name="api:api-docs")),
    path("", include("openforms.api.v2_urls")),
    path("", include("openforms.api.v3_urls", "v3")),
]
