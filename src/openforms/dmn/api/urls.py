from django.urls import path

from .views import (
    DecisionDefinitionInputOutputView,
    DecisionDefinitionListView,
    DecisionDefinitionVersionListView,
    DecisionDefinitionXMLView,
    PluginListView,
)

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="dmn-plugin-list"),
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
    path(
        "decision-definitions/xml",
        DecisionDefinitionXMLView.as_view(),
        name="dmn-definition-xml",
    ),
    path(
        "decision-definitions/inputs-outputs",
        DecisionDefinitionInputOutputView.as_view(),
        name="dmn-definition-inputs-outputs",
    ),
]
