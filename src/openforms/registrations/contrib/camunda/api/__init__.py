from django.urls import path

from .views import ProcessDefinitionListView

app_name = "camunda"

urlpatterns = [
    path(
        "process-definitions",
        ProcessDefinitionListView.as_view(),
        name="process-definitions",
    ),
]
