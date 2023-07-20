from django.urls import path

from .views import MapSearchView

app_name = "geo"

urlpatterns = [
    path(
        "address-search",
        MapSearchView.as_view(),
        name="address-search",
    ),
]
