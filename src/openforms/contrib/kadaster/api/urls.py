from django.urls import path

from .views import AddressAutocompleteView, AddressSearchView, LatLngSearchView

app_name = "geo"

urlpatterns = [
    path(
        "address-autocomplete",
        AddressAutocompleteView.as_view(),
        name="address-autocomplete",
    ),
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
