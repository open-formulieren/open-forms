from django.urls import path

from .views.form import FormDetailView, FormListView

app_name = "forms"

urlpatterns = [
    path("", FormListView.as_view(), name="form-list"),
    path("<slug:slug>/", FormDetailView.as_view(), name="form-detail"),
    path("<slug:slug>/<path:rest>", FormDetailView.as_view(), name="form-detail"),
]
