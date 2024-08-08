from django.urls import path

from .views import CatalogueListView, InformatieObjectTypenListView

app_name = "zgw_apis"

urlpatterns = [
    path(
        "catalogi",
        CatalogueListView.as_view(),
        name="catalogi-list",
    ),
    path(
        "informatieobjecttypen",
        InformatieObjectTypenListView.as_view(),
        name="iotypen-list",
    ),
]
