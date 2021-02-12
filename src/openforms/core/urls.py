from django.urls import path

from .views.form import FormDetailView, FormListView, FormLoginButtonView

app_name = "core"

urlpatterns = [
    path("", FormListView.as_view(), name="form-list"),
    path("<slug:slug>/login", FormLoginButtonView.as_view(), name="form-login"),
    path("<slug:slug>", FormDetailView.as_view(), name="form-detail"),
    path("<slug:slug>/<int:order>", FormDetailView.as_view(), name="form-steps-detail"),
]
