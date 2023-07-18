from django.urls import path

from .views import (
    CancelAppointmentView,
    CreateAppointmentView,
    DatesListView,
    LocationsListView,
    ProductsListView,
    RequiredCustomerFieldsListView,
    TimesListView,
)

urlpatterns = [
    path("products", ProductsListView.as_view(), name="appointments-products-list"),
    path("locations", LocationsListView.as_view(), name="appointments-locations-list"),
    path("dates", DatesListView.as_view(), name="appointments-dates-list"),
    path("times", TimesListView.as_view(), name="appointments-times-list"),
    path(
        "customer-fields",
        RequiredCustomerFieldsListView.as_view(),
        name="appointments-customer-fields",
    ),
    path("appointments", CreateAppointmentView.as_view(), name="appointments-create"),
    path(
        "<uuid:submission_uuid>/cancel",
        CancelAppointmentView.as_view(),
        name="appointments-cancel",
    ),
]
