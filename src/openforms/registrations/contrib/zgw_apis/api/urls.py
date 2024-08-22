from django.urls import path

from .views import CatalogueListView, InformatieObjectTypenListView

app_name = "zgw_apis"

urlpatterns = [
    path(
        "catalogues",
        CatalogueListView.as_view(),
        name="catalogue-list",
    ),
    path(
        "informatieobjecttypen",
        InformatieObjectTypenListView.as_view(),
        name="iotypen-list",
    ),
]
