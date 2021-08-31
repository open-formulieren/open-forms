from django.urls import path

from .views import (
    CancelAppointmentView,
    DatesListView,
    LocationsListView,
    ProductsListView,
    TimesListView,
    VerifyAppointmentView,
)

urlpatterns = [
    path("products", ProductsListView.as_view(), name="appointments-products-list"),
    path("locations", LocationsListView.as_view(), name="appointments-locations-list"),
    path("dates", DatesListView.as_view(), name="appointments-dates-list"),
    path("times", TimesListView.as_view(), name="appointments-times-list"),
    path("verify", VerifyAppointmentView.as_view(), name="appointments-verify"),
    path("cancel", CancelAppointmentView.as_view(), name="appointments-cancel"),
]
