from django.urls import path

from .views import TargetPathsListView

app_name = "registrations_objects_api"

urlpatterns = [
    path(
        "target-paths",
        TargetPathsListView.as_view(),
        name="target-paths",
    )
]
