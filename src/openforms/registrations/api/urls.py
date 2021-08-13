from django.urls import path

from .views import (
    AllAttributesListView,
    PluginListView,
    PluginsConfigurationOptionsView,
)

urlpatterns = [
    path("plugins", PluginListView.as_view(), name="registrations-plugin-list"),
    path(
        "plugins-configuration-options",
        PluginsConfigurationOptionsView.as_view(),
        name="plugins-configuration-options-retrieve",
    ),
    path(
        "attributes",
        AllAttributesListView.as_view(),
        name="registrations-attribute-list",
    ),
]
