from django.urls import path

from .views import PluginListView, ProcessDefinitionListView

app_name = "camunda"

urlpatterns = [
    path(
        "process-definitions",
        ProcessDefinitionListView.as_view(),
        name="process-definitions",
    ),
    path(
        "plugins",
        PluginListView.as_view(),
        name="plugins",
    ),
]
