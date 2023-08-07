from django.urls import path

from .views import AddressSearchView, LatLngSearchView

app_name = "geo"

urlpatterns = [
    path(
        "address-search",
        AddressSearchView.as_view(),
        name="address-search",
    ),
    path(
        "latlng-search",
        LatLngSearchView.as_view(),
        name="latlng-search",
    ),
]
