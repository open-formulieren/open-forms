from django.urls import path

from .views import TemporaryFileUploadView

app_name = "formio"

urlpatterns = [
    path(
        "files/upload",
        TemporaryFileUploadView.as_view(),
        name="temporary-file-upload",
    ),
]
