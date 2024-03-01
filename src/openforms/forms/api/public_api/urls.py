from django.urls import path

from .views import FormListView

app_name = "forms"

urlpatterns = [
    path(
        "",
        FormListView.as_view(),
        name="forms-list",
    ),
]
