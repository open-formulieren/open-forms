from django.urls import path

from .views import ZaakTypenListView

app_name = "zgw_api"

urlpatterns = [
    path(
        "zaaktypen",
        ZaakTypenListView.as_view(),
        name="zaaktypen-list",
    ),
]
