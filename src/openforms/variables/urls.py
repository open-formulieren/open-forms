from django.urls import path

from .api.views import RegistrationPluginVariablesView, StaticFormVariablesView

app_name = "variables"

urlpatterns = [
    path(
        "static",
        StaticFormVariablesView.as_view(),
        name="static",
    ),
    path(
        "registration",
        RegistrationPluginVariablesView.as_view(),
        name="registration",
    ),
]
