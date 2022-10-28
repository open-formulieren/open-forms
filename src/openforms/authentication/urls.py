from django.urls import path

from .views import (
    AuthenticationReturnView,
    AuthenticationStartView,
    RegistratorSubjectInfoView,
)

app_name = "authentication"

urlpatterns = [
    path(
        "<slug:slug>/registrator-subject",
        RegistratorSubjectInfoView.as_view(),
        name="registrator-subject",
    ),
    path(
        "<slug:slug>/<slug:plugin_id>/start",
        AuthenticationStartView.as_view(),
        name="start",
    ),
    path(
        "<slug:slug>/<slug:plugin_id>/return",
        AuthenticationReturnView.as_view(),
        name="return",
    ),
]
