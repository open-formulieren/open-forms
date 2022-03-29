from django.urls import path

from .views import (
    DecisionDefinitionListView,
    DecisionDefinitionVersionListView,
    PluginListView,
)

urlpatterns = [
    path(
        "decision-definitions",
        DecisionDefinitionListView.as_view(),
        name="dmn-definition-list",
    ),
    path(
        "decision-definitions/versions",
        DecisionDefinitionVersionListView.as_view(),
        name="dmn-definition-version-list",
    ),
    path("plugins", PluginListView.as_view(), name="dmn-plugin-list"),
]
