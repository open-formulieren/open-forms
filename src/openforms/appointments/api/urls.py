from django.urls import path

from .views import (
    CancelAppointmentView,
    DatesListView,
    LocationsListView,
    ProductsListView,
    TimesListView,
)

urlpatterns = [
    path("products", ProductsListView.as_view(), name="appointments-products-list"),
    path("locations", LocationsListView.as_view(), name="appointments-locations-list"),
    path("dates", DatesListView.as_view(), name="appointments-dates-list"),
    path("times", TimesListView.as_view(), name="appointments-times-list"),
    path(
        "<uuid:submission_uuid>/cancel",
        CancelAppointmentView.as_view(),
        name="appointments-cancel",
    ),
]
