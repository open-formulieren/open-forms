from django.urls import path

from .views import LocationsListView, ProductsListView

urlpatterns = [
    path("products", ProductsListView.as_view(), name="jcc-products-list"),
    path("locations", LocationsListView.as_view(), name="jcc-locations-list"),
]
