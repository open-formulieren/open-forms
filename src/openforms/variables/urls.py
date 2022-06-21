from django.urls import path

from .views import StaticFormVariablesView

app_name = "variables"

urlpatterns = [
    path(
        "static",
        StaticFormVariablesView.as_view(),
        name="static",
    )
]
