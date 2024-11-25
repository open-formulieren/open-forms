from django.urls import path

from .views import (
    CatalogueListView,
    DocumentTypesListView,
    ObjecttypesListView,
    ObjecttypeVersionsListView,
)

app_name = "objects_api"

urlpatterns = [
    path(
        "object-types",
        ObjecttypesListView.as_view(),
        name="object-types",
    ),
    path(
        "object-types/<uuid:objecttype_uuid>/versions",
        ObjecttypeVersionsListView.as_view(),
        name="object-type-versions",
    ),
    path(
        "catalogues",
        CatalogueListView.as_view(),
        name="catalogue-list",
    ),
    path(
        "document-types",
        DocumentTypesListView.as_view(),
        name="document-type-list",
    ),
]
