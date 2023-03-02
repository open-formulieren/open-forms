from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.ServiceListView.as_view(),
        name="service-list",
    ),
]
