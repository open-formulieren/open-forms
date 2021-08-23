from django.urls import path

from .views import DatesListView, LocationsListView, ProductsListView, TimesListView

urlpatterns = [
    path("products", ProductsListView.as_view(), name="jcc-products-list"),
    path("locations", LocationsListView.as_view(), name="jcc-locations-list"),
    path("dates", DatesListView.as_view(), name="jcc-dates-list"),
    path("times", TimesListView.as_view(), name="jcc-times-list"),
]
