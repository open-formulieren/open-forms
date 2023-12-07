from django.urls import path

from .views.form import FormDetailView, FormListView, ThemePreviewFormView

app_name = "forms"

urlpatterns = [
    # for staff users only
    path(
        "internal/theme-preview/<int:theme_pk>/<slug:slug>",
        ThemePreviewFormView.as_view(),
        name="theme-preview",
    ),
    path(
        "internal/theme-preview/<int:theme_pk>/<slug:slug>/<path:rest>",
        ThemePreviewFormView.as_view(),
        name="theme-preview",
    ),
    # sometimes-public URLs
    path("", FormListView.as_view(), name="form-list"),
    # public URLs
    path("<slug:slug>/", FormDetailView.as_view(), name="form-detail"),
    path("<slug:slug>/<path:rest>", FormDetailView.as_view(), name="form-detail"),
]
