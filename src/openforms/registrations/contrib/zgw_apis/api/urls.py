from django.urls import path

from .views import InformatieObjectTypenListView

app_name = "zgw_apis"

urlpatterns = [
    path(
        "informatieobjecttypen",
        InformatieObjectTypenListView.as_view(),
        name="iotypen-list",
    ),
]
