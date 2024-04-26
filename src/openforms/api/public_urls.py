from django.urls import include, path

app_name = "public"

urlpatterns = [
    path("forms", include("openforms.forms.api.public_api.urls")),
]
