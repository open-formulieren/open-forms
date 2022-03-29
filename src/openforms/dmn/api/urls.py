from django.urls import path

from .views import DecisionDefinitionListView, PluginListView

urlpatterns = [
    path(
        "decision-definitions",
        DecisionDefinitionListView.as_view(),
        name="dmn-definition-list",
    ),
    path("plugins", PluginListView.as_view(), name="dmn-plugin-list"),
]
