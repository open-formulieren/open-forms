from django.urls import path

from .views import (
    AllAttributesListView,
    PluginConfigurationOptionsJsonSchemaView,
    PluginListView,
)

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="registrations-plugin-list"),
    path(
        "plugin-configuration-options",
        PluginConfigurationOptionsJsonSchemaView.as_view(),
        name="plugin-configuration-options-jsonschema-retrieve",
    ),
    path(
        "attributes",
        AllAttributesListView.as_view(),
        name="registrations-attribute-list",
    ),
]
