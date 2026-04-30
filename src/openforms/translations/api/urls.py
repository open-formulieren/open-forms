from django.urls import path

from .views import (
    CustomizedCompiledTranslations,
    LanguageInfoView,
    SetLanguageView,
)

app_name = "i18n"

urlpatterns = [
    path("info", LanguageInfoView.as_view(), name="info"),
    path("language", SetLanguageView.as_view(), name="language"),
    path(
        "compiled-messages/<str:language_code>.json",
        CustomizedCompiledTranslations.as_view(),
        name="customized-translations",
    ),
]
