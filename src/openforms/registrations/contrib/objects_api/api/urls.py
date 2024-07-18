from django.urls import path

from .views import (
    CatalogiListView,
    InformatieObjectTypenListView,
    ObjecttypesListView,
    ObjecttypeVersionsListView,
    TargetPathsListView,
)

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
    path(
        "target-paths",
        TargetPathsListView.as_view(),
        name="target-paths",
    ),
    path(
        "catalogi",
        CatalogiListView.as_view(),
        name="catalogi-list",
    ),
    path(
        "informatieobjecttypen",
        InformatieObjectTypenListView.as_view(),
        name="iotypen-list",
    ),
]
