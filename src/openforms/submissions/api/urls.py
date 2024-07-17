from django.urls import path

from .views import TemporaryFileView

app_name = "submissions"

urlpatterns = [
    path(
        "files/<uuid:uuid>",
        TemporaryFileView.as_view(),
        name="temporary-file",
    ),
]
