from django.urls import path

from .views import current_language, info

app_name = "i18n"

urlpatterns = [
    path("info", info, name="info"),
    path("language", current_language, name="language"),
]
