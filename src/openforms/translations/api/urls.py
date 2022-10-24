from django.urls import path

from .views import info

app_name = "i18n"

urlpatterns = [
    path("info", info, name="info"),
]
