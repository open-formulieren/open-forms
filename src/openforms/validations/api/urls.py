from django.urls import path

from .views import ValidationView, ValidatorsListView

urlpatterns = [
    path("plugins", ValidatorsListView.as_view(), name="validators-list"),
    path(
        "plugins/<slug:validator>",
        ValidationView.as_view(),
        name="validate-value",
    ),
]
