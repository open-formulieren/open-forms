from django.urls import path

from .views import ObjecttypesListView, ObjecttypeVersionsListView

app_name = "objects_api"

urlpatterns = [
    path(
        "object-types",
        ObjecttypesListView.as_view(),
        name="object-types",
    ),
    path(
        "object-types/<uuid:submission_uuid>/versions",
        ObjecttypeVersionsListView.as_view(),
        name="object-type-versions",
    ),
]
