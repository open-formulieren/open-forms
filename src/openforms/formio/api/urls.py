from django.urls import path

from .views import MapSearchView, TemporaryFileUploadView

app_name = "formio"

urlpatterns = [
    path(
        "fileupload",
        TemporaryFileUploadView.as_view(),
        name="temporary-file-upload",
    ),
    path(
        "mapsearch",
        MapSearchView.as_view(),
        name="map-search",
    ),
]
