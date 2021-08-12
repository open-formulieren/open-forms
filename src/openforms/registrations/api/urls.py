from django.urls import path

from .views import (
    AllAttributesListView,
    PluginsConfigurationOptionsJsonSchemaView,
    PluginListView,
)

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="registrations-plugin-list"),
    path(
        "plugins-configuration-options",
        PluginsConfigurationOptionsJsonSchemaView.as_view(),
        name="plugins-configuration-options-jsonschema-retrieve",
    ),
    path(
        "attributes",
        AllAttributesListView.as_view(),
        name="registrations-attribute-list",
    ),
]
