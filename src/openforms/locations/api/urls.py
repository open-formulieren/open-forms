from django.urls import path

from .views import GetStreetNameAndCityView

urlpatterns = [
    path(
        "get-street-name-and-city",
        GetStreetNameAndCityView.as_view(),
        name="get-street-name-and-city-list",
    ),
]
