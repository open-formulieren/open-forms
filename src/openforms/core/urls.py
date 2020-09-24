from django.urls import path

from .views.form import FormListView, FormDetailView

app_name = 'core'

urlpatterns = [
    path("", FormListView.as_view(), name="form-list"),
    path("<slug:slug>", FormDetailView.as_view(), name="form-detail")
]
