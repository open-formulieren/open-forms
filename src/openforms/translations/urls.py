from django.urls import path

from .views import FormIOTranslationsView

app_name = "translations"

urlpatterns = [
    path(
        "formio",
        FormIOTranslationsView.as_view(),
        name="formio-translations",
    )
]
