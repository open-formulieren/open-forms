from django.urls import path

from .views import FixedMetadataVariablesView

app_name = "registrations_generic_json"

urlpatterns = [
    path(
        "fixed-metadata-variables",
        FixedMetadataVariablesView.as_view(),
        name="fixed_metadata_variables",
    )
]
