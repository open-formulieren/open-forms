from django.urls import path

from .views import AddressSearchView

app_name = "geo"

urlpatterns = [
    path(
        "address-search",
        AddressSearchView.as_view(),
        name="address-search",
    ),
]
