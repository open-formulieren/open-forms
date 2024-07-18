from django.urls import path

from .views import CatalogiListView, InformatieObjectTypenListView

app_name = "zgw_apis"

urlpatterns = [
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
