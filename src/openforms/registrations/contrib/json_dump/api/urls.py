from django.urls import path

from .views import FixedMetadataVariablesView

app_name = "registrations_json_dump"

urlpatterns = [
    path(
        "fixed-metadata-variables",
        FixedMetadataVariablesView.as_view(),
        name="fixed_metadata_variables",
    )
]
