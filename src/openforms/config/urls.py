from django.urls import path

from .views import ConfigurationView

app_name = "config"

urlpatterns = [
    path("overview/", ConfigurationView.as_view(), name="overview"),
]
