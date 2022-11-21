from django.urls import path

from .views import FormioTranslationsView, LanguageInfoView, SetLanguageView

app_name = "i18n"

urlpatterns = [
    path("info", LanguageInfoView.as_view(), name="info"),
    path("language", SetLanguageView.as_view(), name="language"),
    path(
        "formio/<str:language>",
        FormioTranslationsView.as_view(),
        name="formio-translations",
    ),
]
